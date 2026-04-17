/* ═══════════════════════════════════════════════════════
   CAMPUSTALLY — Persistent Data Layer (localStorage)
   ═══════════════════════════════════════════════════════

   Storage keys:
   ─────────────────────────────────────────────────────
   ct_users          { [studentId]: UserObject }
   ct_current_user   studentId string
   ct_admin_session  '1' | null
   ct_elections      ElectionObject[]
   ct_votes          { [userId]: { [elKey]: candidateIndex } }
   ct_activity       { [userId]: ActivityItem[] }
   ═══════════════════════════════════════════════════════ */

// ─── STORAGE HELPERS ──────────────────────────────────
const DB = {
  get(key)        { try { return JSON.parse(localStorage.getItem(key)); } catch { return null; } },
  set(key, value) { localStorage.setItem(key, JSON.stringify(value)); },
  del(key)        { localStorage.removeItem(key); }
};

// ─── TOAST ────────────────────────────────────────────
function toast(msg, type) {
  type = type || '';
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(function() { el.remove(); }, 3200);
}

// ─── PASSWORD TOGGLE ──────────────────────────────────
function togglePw(inputId, btn) {
  const inp = document.getElementById(inputId);
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁️' : '🙈';
}

// ─── DATE HELPERS ─────────────────────────────────────
function fmtTime(ts) {
  return new Date(ts).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', hour12: true
  });
}

// ═══════════════════════════════════════════════════════
//  USERS
// ═══════════════════════════════════════════════════════
function getUsers()       { return DB.get('ct_users') || {}; }
function saveUsers(users) { DB.set('ct_users', users); }

function registerUser(data) {
  var users = getUsers();
  if (users[data.id]) return { ok: false, error: 'Student ID already registered.' };
  users[data.id] = {
    name: data.name, id: data.id, index: data.index,
    course: data.course, password: data.password,
    createdAt: Date.now(), votingStatus: 'Verified', level: '400'
  };
  saveUsers(users);
  DB.set('ct_current_user', data.id);
  return { ok: true, user: users[data.id] };
}

function loginUser(id, password) {
  var users = getUsers();
  // First-ever login: auto-create demo account
  if (!users[id] && Object.keys(users).length === 0) {
    var demo = { name: 'Ephraim Boaitey', id: id, index: 'UEB1108022',
                 course: 'B.Sc. Computer Engineering', password: password,
                 createdAt: Date.now(), votingStatus: 'Verified', level: '400' };
    users[id] = demo;
    saveUsers(users);
    DB.set('ct_current_user', id);
    return { ok: true, user: demo };
  }
  if (!users[id]) return { ok: false, error: 'Student ID not found.' };
  if (users[id].password !== password) return { ok: false, error: 'Incorrect password.' };
  DB.set('ct_current_user', id);
  return { ok: true, user: users[id] };
}

function getCurrentUser() {
  var id = DB.get('ct_current_user');
  if (!id) return null;
  return getUsers()[id] || null;
}

function logoutUser() { DB.del('ct_current_user'); }

// ═══════════════════════════════════════════════════════
//  ADMIN SESSION
// ═══════════════════════════════════════════════════════
function adminLogin(id, password) {
  if (id === 'admin' && password === 'admin123') {
    DB.set('ct_admin_session', '1');
    return true;
  }
  return false;
}
function isAdmin()      { return DB.get('ct_admin_session') === '1'; }
function doAdminLogout() { DB.del('ct_admin_session'); }

// ═══════════════════════════════════════════════════════
//  ELECTIONS
// ═══════════════════════════════════════════════════════
function getElections() {
  var list = DB.get('ct_elections');
  if (!list) { list = defaultElections(); DB.set('ct_elections', list); }
  return list;
}
function saveElections(list) { DB.set('ct_elections', list); }

function getElectionById(id) {
  return getElections().find(function(e) { return e.id === id; }) || null;
}

function createElection(data) {
  var list = getElections();
  var election = Object.assign({ id: 'el_' + Date.now(), createdAt: Date.now() }, data);
  list.push(election);
  saveElections(list);
  return election;
}

function updateElection(id, updates) {
  var list = getElections();
  var idx  = list.findIndex(function(e) { return e.id === id; });
  if (idx === -1) return false;
  list[idx] = Object.assign({}, list[idx], updates);
  saveElections(list);
  return true;
}

function deleteElection(id) {
  saveElections(getElections().filter(function(e) { return e.id !== id; }));
}

// ═══════════════════════════════════════════════════════
//  VOTES
// ═══════════════════════════════════════════════════════
function getAllVotes()        { return DB.get('ct_votes') || {}; }
function saveAllVotes(votes)  { DB.set('ct_votes', votes); }

function getUserVotes(userId) {
  return getAllVotes()[userId] || {};
}

function castVote(userId, electionId, positionIndex, candidateIndex) {
  var all = getAllVotes();
  if (!all[userId]) all[userId] = {};
  all[userId][electionId + '__' + positionIndex] = candidateIndex;
  saveAllVotes(all);
  logActivity(userId, {
    type: 'vote', electionId: electionId,
    positionIndex: positionIndex, candidateIndex: candidateIndex,
    timestamp: Date.now()
  });
}

function hasVotedInElection(userId, electionId) {
  var uv = getUserVotes(userId);
  return Object.keys(uv).some(function(k) { return k.indexOf(electionId + '__') === 0; });
}

function getVoteForPosition(userId, electionId, positionIndex) {
  var uv  = getUserVotes(userId);
  var key = electionId + '__' + positionIndex;
  return uv[key] !== undefined ? uv[key] : null;
}

// Tally real + seed votes for one position
function tallyPosition(electionId, positionIndex, candidateCount) {
  var counts   = [];
  var i;
  for (i = 0; i < candidateCount; i++) counts.push(0);

  var election = getElectionById(electionId);
  if (election && election.seedVotes && election.seedVotes[positionIndex]) {
    election.seedVotes[positionIndex].forEach(function(n, i) { counts[i] += n; });
  }

  var all = getAllVotes();
  var key = electionId + '__' + positionIndex;
  Object.values(all).forEach(function(uv) {
    if (uv[key] !== undefined && uv[key] >= 0 && uv[key] < candidateCount) {
      counts[uv[key]]++;
    }
  });

  var total = counts.reduce(function(a, b) { return a + b; }, 0);
  return counts.map(function(n, idx) {
    return { index: idx, votes: n, pct: total > 0 ? Math.round((n / total) * 100) : 0 };
  });
}

// ═══════════════════════════════════════════════════════
//  ACTIVITY LOG
// ═══════════════════════════════════════════════════════
function getActivity(userId) {
  return (DB.get('ct_activity') || {})[userId] || [];
}

function logActivity(userId, item) {
  var all = DB.get('ct_activity') || {};
  if (!all[userId]) all[userId] = [];
  all[userId].unshift(item);
  if (all[userId].length > 50) all[userId] = all[userId].slice(0, 50);
  DB.set('ct_activity', all);
}

// ═══════════════════════════════════════════════════════
//  STATS
// ═══════════════════════════════════════════════════════
function getTotalVotesCast() {
  var total = 0;
  getElections().forEach(function(el) {
    if (el.seedVotes) {
      el.seedVotes.forEach(function(posArr) {
        posArr.forEach(function(n) { total += n; });
      });
    }
  });
  Object.values(getAllVotes()).forEach(function(uv) {
    total += Object.keys(uv).length;
  });
  return total;
}

function getRegisteredCount() { return Object.keys(getUsers()).length; }

// ═══════════════════════════════════════════════════════
//  TIMERS
// ═══════════════════════════════════════════════════════
function startCountdown(elementId, hours) {
  var el = document.getElementById(elementId);
  if (!el) return;
  var seconds = hours * 3600;
  function tick() {
    seconds = Math.max(0, seconds - 1);
    var h = String(Math.floor(seconds / 3600)).padStart(2, '0');
    var m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
    var s = String(seconds % 60).padStart(2, '0');
    el.textContent = h + ':' + m + ':' + s;
  }
  tick();
  setInterval(tick, 1000);
}

// ═══════════════════════════════════════════════════════
//  DEFAULT ELECTION DATA  (seeded on first load)
// ═══════════════════════════════════════════════════════
function defaultElections() {
  return [
    {
      id: 'src_2024', title: 'SRC General Election 2024', shortName: 'SRC Elections',
      category: 'SRC Election', status: 'active',
      startDate: '2024-10-20', startTime: '08:00',
      endDate:   '2024-10-26', endTime:   '18:00',
      createdAt: Date.now() - 86400000 * 4,
      seedVotes: [
        [2340, 1820, 1040],
        [2640, 1494,  847],
        [3193, 1957,    0],
        [2200, 1800, 1200],
        [1900, 1500,  900]
      ],
      positions: [
        { title: 'SRC President', candidates: [
          { name: 'Guru',     emoji: '👤', info: { role: 'SRC Presidential Candidate',      score: '87/100', manifesto: 'A New Dawn for Students', body: 'I pledge to improve student welfare, reduce bureaucracy, and create a more transparent SRC. My key areas include infrastructure, academic support, and student mental health.', policies: ['Free printing stations in all labs', '24/7 student counselling centre'] } },
          { name: 'Akrobeto', emoji: '👤', info: { role: 'SRC Presidential Candidate',      score: '82/100', manifesto: 'Students First Always',    body: 'Together we can build a stronger student body. My vision covers improved facilities, better representation, and stronger industry partnerships.', policies: ['Discounted transport scheme', 'Industry attachment facilitation'] } },
          { name: 'Lilwin',   emoji: '👤', info: { role: 'SRC Presidential Candidate',      score: '75/100', manifesto: 'Rising Together',          body: 'A grassroots approach to student leadership focused on unity and progress for every department.', policies: ['Monthly SRC open forums', 'Departmental grant fund'] } }
        ]},
        { title: 'SRC Vice President', candidates: [
          { name: 'Asamoah Gyan', emoji: '👤', info: { role: 'SRC Vice Presidential Candidate', score: '88/100', manifesto: 'Supporting Every Student', body: 'Bridging the gap between students and administration with transparency and action.', policies: ['Student ID card discounts', 'Extended library hours'] } },
          { name: 'Kwame Messi',  emoji: '👤', info: { role: 'SRC Vice Presidential Candidate', score: '79/100', manifesto: 'Empowering the Youth',     body: 'A youth-first agenda prioritising innovation and entrepreneurship on campus.', policies: ['Startup incubator', 'Mentorship programs'] } },
          { name: 'Yaw Ronaldo',  emoji: '👤', info: { role: 'SRC Vice Presidential Candidate', score: '71/100', manifesto: 'Fairness for All',          body: 'Equal opportunities for every student regardless of background or department.', policies: ['Scholarship awareness drive', 'Welfare fund expansion'] } }
        ]},
        { title: 'SRC General Secretary', candidates: [
          { name: 'Russell Kusi', emoji: '👤', info: { role: 'SRC General Secretary Candidate', score: '90/100', manifesto: 'Transparency & Accountability', body: 'Complete overhaul of SRC record-keeping and communication channels for all students.', policies: ['Monthly financial reports', 'Open SRC minutes'] } },
          { name: 'Haleem Abdul', emoji: '👤', info: { role: 'SRC General Secretary Candidate', score: '84/100', manifesto: 'Organized & Efficient',         body: 'Streamlining SRC operations and administration for maximum student benefit.', policies: ['Digital SRC portal', 'Online petition system'] } },
          { name: 'Gibson Ofori', emoji: '👤', info: { role: 'SRC General Secretary Candidate', score: '77/100', manifesto: 'Service Before Self',           body: 'Committed to serving students with humility, dedication and transparency.', policies: ['Student grievance hotline', 'Suggestion boxes across campus'] } }
        ]},
        { title: 'SRC Financial Secretary', candidates: [
          { name: 'Ken Ofori Atta', emoji: '👤', info: { role: 'SRC Financial Secretary Candidate', score: '92/100', manifesto: 'Fiscal Responsibility',  body: 'Prudent management of SRC funds for maximum impact and accountability.', policies: ['Quarterly budget audits', 'Student welfare fund'] } },
          { name: 'Ato Forson',     emoji: '👤', info: { role: 'SRC Financial Secretary Candidate', score: '86/100', manifesto: 'Every Pesewa Counts',    body: 'Zero wastage policy and fully transparent financial reporting to all students.', policies: ['Digital receipts for all transactions', 'Bursary fund expansion'] } },
          { name: 'Wayomi',         emoji: '👤', info: { role: 'SRC Financial Secretary Candidate', score: '73/100', manifesto: 'Invest in Students',      body: 'Redirecting SRC funds to directly and measurably benefit students.', policies: ['Free printing credits', 'Emergency student fund'] } }
        ]},
        { title: "SRC Women's Commissioner", candidates: [
          { name: 'Abena Korkor', emoji: '👤', info: { role: "Women's Commissioner Candidate", score: '89/100', manifesto: 'Women Rising',       body: 'Championing gender equality and women safety on campus through policy and action.', policies: ['Safe walk program', 'Women mentorship series'] } },
          { name: 'Nana Ama',     emoji: '👤', info: { role: "Women's Commissioner Candidate", score: '83/100', manifesto: 'Her Voice Matters',  body: 'Amplifying women voices in every corner of student governance and campus life.', policies: ['Monthly women town halls', 'Sanitary product subsidies'] } },
          { name: 'Efua Bright',  emoji: '👤', info: { role: "Women's Commissioner Candidate", score: '76/100', manifesto: 'Together We Shine',  body: 'Building a supportive and empowered community for all women on campus.', policies: ['Women safety app', 'Female leadership training'] } }
        ]}
      ]
    },
    {
      id: 'nugs_2024', title: 'Local NUGS Elections 2024', shortName: 'Local NUGS',
      category: 'NUGS Election', status: 'active',
      startDate: '2024-10-20', startTime: '08:00',
      endDate:   '2024-10-26', endTime:   '18:00',
      createdAt: Date.now() - 86400000 * 3,
      seedVotes: [
        [2640, 2160,  800],
        [2200, 1700, 1100],
        [3000, 1800,  600],
        [2500, 1500, 1200],
        [1900, 1600, 1000]
      ],
      positions: [
        { title: 'LNUGS President', candidates: [
          { name: 'Mama Pat', emoji: '👤', info: { role: 'LNUGS Presidential Candidate', score: '91/100', manifesto: 'For All Students',  body: 'Building bridges between NUGS and the student body through grassroots engagement.', policies: ['NUGS welfare fund', 'Industry engagement nights'] } },
          { name: 'Delay',    emoji: '👤', info: { role: 'LNUGS Presidential Candidate', score: '85/100', manifesto: 'Progress & Unity',  body: 'A progressive agenda for the National Union of Ghana Students built on unity.', policies: ['National student network', 'Joint campus events'] } },
          { name: 'Tupac',    emoji: '👤', info: { role: 'LNUGS Presidential Candidate', score: '72/100', manifesto: 'Student Power',     body: 'Uniting students under one powerful, inclusive voice for change.', policies: ['Student solidarity fund', 'Advocacy campaigns'] } }
        ]},
        { title: 'LNUGS Vice President', candidates: [
          { name: 'Akabenezer',  emoji: '👤', info: { role: 'LNUGS Vice Presidential Candidate', score: '87/100', manifesto: 'Action & Results', body: 'Focused on delivering tangible and measurable results for all students.', policies: ['Internship database', 'Study resources portal'] } },
          { name: 'Kwame Alidu', emoji: '👤', info: { role: 'LNUGS Vice Presidential Candidate', score: '80/100', manifesto: 'Students United',   body: 'Unifying diverse student groups under one strong NUGS umbrella.', policies: ['Cross-campus dialogues', 'Cultural exchange program'] } },
          { name: 'Yaw Mensah',  emoji: '👤', info: { role: 'LNUGS Vice Presidential Candidate', score: '74/100', manifesto: 'Bold Leadership',   body: 'Leading with courage, vision and empathy for the whole student community.', policies: ['Leadership bootcamp', 'Youth entrepreneurship fund'] } }
        ]},
        { title: 'LNUGS General Secretary', candidates: [
          { name: 'Russell Kusi', emoji: '👤', info: { role: 'LNUGS General Secretary Candidate', score: '90/100', manifesto: 'Efficient & Open',      body: 'Bringing modern management practices to NUGS administration.', policies: ['Digital communication', 'Weekly updates to members'] } },
          { name: 'Haleem Abdul', emoji: '👤', info: { role: 'LNUGS General Secretary Candidate', score: '83/100', manifesto: 'Serving with Excellence', body: 'Committed to administrative excellence and total student welfare.', policies: ['NUGS member newsletter', 'Open forum meetings'] } },
          { name: 'Gibson Ofori', emoji: '👤', info: { role: 'LNUGS General Secretary Candidate', score: '77/100', manifesto: 'Accountability First',   body: 'Transparent, accountable NUGS secretariat for every student.', policies: ['Published meeting minutes', 'Annual NUGS report'] } }
        ]},
        { title: 'LNUGS Financial Secretary', candidates: [
          { name: 'Ken Ofori Atta', emoji: '👤', info: { role: 'LNUGS Financial Secretary Candidate', score: '93/100', manifesto: 'Responsible Finance', body: 'Strategic, prudent management of NUGS finances for maximum student impact.', policies: ['Financial transparency dashboard', 'Emergency student grants'] } },
          { name: 'Ato Forson',     emoji: '👤', info: { role: 'LNUGS Financial Secretary Candidate', score: '87/100', manifesto: 'Smart Spending',      body: 'Maximising the impact of every single student contribution and levy.', policies: ['Cost-benefit reviews', 'Student discount partnerships'] } },
          { name: 'Wayomi',         emoji: '👤', info: { role: 'LNUGS Financial Secretary Candidate', score: '74/100', manifesto: 'Invest Wisely',        body: 'Building long-term financial reserves that benefit every generation of students.', policies: ['Savings scheme for students', 'Annual bursary awards'] } }
        ]},
        { title: "LNUGS Women's Commissioner", candidates: [
          { name: 'Adwoa Sarfo',    emoji: '👤', info: { role: "Women's Commissioner Candidate", score: '88/100', manifesto: 'Women Empowered', body: 'Creating safe, empowering spaces for all women across campus and beyond.', policies: ['Safe campus initiative', 'Women leadership summits'] } },
          { name: 'Gifty Anti',     emoji: '👤', info: { role: "Women's Commissioner Candidate", score: '82/100', manifesto: "Her Future Now",  body: 'Investing boldly in the futures and potential of every woman on campus.', policies: ['Skills training for women', 'Scholarship drive'] } },
          { name: 'Serwaa Amihere', emoji: '👤', info: { role: "Women's Commissioner Candidate", score: '76/100', manifesto: 'Voices Heard',    body: 'Ensuring every women\'s voice is heard at every decision-making table.', policies: ['Women advisory council', 'Gender policy review'] } }
        ]}
      ]
    },
    {
      id: 'eng_2024', title: 'School of Engineering Elections', shortName: 'School of Engineering',
      category: 'Faculty / School', status: 'upcoming',
      startDate: '2024-10-28', startTime: '08:00',
      endDate:   '2024-10-29', endTime:   '18:00',
      createdAt: Date.now() - 86400000,
      seedVotes: [],
      positions: [
        { title: 'Engineering President', candidates: [
          { name: 'Kwesi Mensah', emoji: '👤', info: { role: 'Engineering Presidential Candidate', score: '91/100', manifesto: 'Engineering the Future', body: 'A strong, dedicated voice for all engineering students on campus.', policies: ['Lab access extension', 'Industry visits program'] } },
          { name: 'Abena Asante', emoji: '👤', info: { role: 'Engineering Presidential Candidate', score: '85/100', manifesto: 'Innovation First',        body: 'Driving innovation, collaboration and excellence within the faculty.', policies: ['Hackathon series', 'Equipment grants'] } }
        ]}
      ]
    },
    {
      id: 'dept_2023', title: 'Departmental / Assocs Elections 2023', shortName: 'Departmental / Assocs',
      category: 'Departmental', status: 'closed',
      startDate: '2023-10-15', startTime: '08:00',
      endDate:   '2023-10-16', endTime:   '18:00',
      createdAt: Date.now() - 86400000 * 30,
      seedVotes: [ [1400, 1100] ],
      positions: [
        { title: 'CS Dept. President', candidates: [
          { name: 'Emmanuel Tetteh', emoji: '👤', info: { role: 'CS Dept. Presidential Candidate', score: '94/100', manifesto: 'Code the Change',  body: 'Empowering CS students with better resources, tools and industry links.', policies: ['Free cloud credits', 'Internship network'] } },
          { name: 'Grace Addo',      emoji: '👤', info: { role: 'CS Dept. Presidential Candidate', score: '88/100', manifesto: 'Inclusive Tech',    body: 'Building an inclusive, supportive and thriving CS student community.', policies: ['Study groups fund', 'Open source contribution drive'] } }
        ]}
      ]
    }
  ];
}
