
// ─── ENVIRONMENT ──────────────────────────────────────────────────────────────
// Inlined from env.js (which uses ES module syntax and can't be imported here).
var _BASE_API = (function () {
  var isDev = window.location.href.includes('localhost') ||
              window.location.href.includes('127.0.0.1');
  return isDev ? 'http://localhost:8000/api' : 'https://campus-tally-backend.onrender.com/api';
}());


// ─── ROUTES ───────────────────────────────────────────────────────────────────
// Inlined from route.js (which uses export default and can't be imported here).
var _R = {
  user_signup:   '/auth/signup',
  user_login:    '/auth/login',
  user_me:       '/auth/me',
  admin_login:   '/admin/login',
  admin_add:     '/admin/add',
  admin_remove:  '/admin/remove',
  elections_all: '/elections/all',
  election:      function (id) { return '/elections/' + id; },
  election_create: '/elections/create',
  election_update: function (id) { return '/elections/update/' + id; },
  election_delete: function (id) { return '/elections/delete/' + id; },
  vote_cast:     '/votes/cast',
  votes_by_user: function (uid) { return '/votes/user/' + uid; },
  votes_by_election: function (eid) { return '/votes/election/' + eid; },
  stats:         function (eid) { return '/stats/election/' + eid; },
  stats_overview:'/stats/overview',
  activity:      '/activity',
  activity_user: function (uid) { return '/activity/' + uid; }
};


// ─── CACHE HELPERS ────────────────────────────────────────────────────────────
// A thin wrapper around localStorage that handles JSON safely.
// All cache keys are prefixed 'ct_' to avoid collisions.
var _C = {
  get: function (key) {
    return JSON.parse(localStorage.getItem(key))
  },
  set: function (key, val) {
    localStorage.setItem(key, JSON.stringify(val));
  },
  del: function (key) { localStorage.removeItem(key); }
};

// Cache key constants
var _CK = {
  USER_TOKEN:    'ct_token',
  ADMIN_TOKEN:   'ct_admin_token',
  USER:          'ct_user',
  ELECTIONS:     'ct_elections',
  VOTES:         'ct_votes',       // { "elId__posIdx": candidateIndex }
  STATS:         'ct_stats',       // { elId: { totalVotes, positions:[...] } }
  ACTIVITY:      'ct_activity',    // { userId: ActivityItem[] }
  REGISTERED:    'ct_registered'   // integer count
};


// ─── BACKWARD-COMPAT DB SHIM ──────────────────────────────────────────────────
// admin-dashboard.html calls DB.set('ct_admin_session', ...).
// We keep this object so it doesn't throw, but it's not used for auth anymore.
var DB = {
  get: _C.get,
  set: _C.set,
  del: _C.del
};


// ═══════════════════════════════════════════════════════════════════════════════
//  UI UTILITIES
//  These are pure DOM helpers. They are synchronous and have no API dependency.
// ═══════════════════════════════════════════════════════════════════════════════

function toast(msg, type) {
  type = type || '';
  var container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  var el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(function () { el.remove(); }, 3200);
}

function togglePw(inputId, btn) {
  var inp = document.getElementById(inputId);
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁️' : '🙈';
}

function fmtTime(ts) {
  return new Date(ts).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', hour12: true
  });
}

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


// ═══════════════════════════════════════════════════════════════════════════════
//  CORE FETCH
//  All network calls go through _request() and _adminRequest().
//  They always resolve (never reject) with { ok, data } | { ok, error }
//  so callers never need try/catch around individual calls.
// ═══════════════════════════════════════════════════════════════════════════════

function _headers(adminMode) {
  var token = adminMode ? _C.get(_CK.ADMIN_TOKEN) : _C.get(_CK.USER_TOKEN);
  var h = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = 'Bearer ' + token;
  return h;
}

async function _request(method, endpoint, body, adminMode) {
  try {
    var opts = { method: method, headers: _headers(adminMode || false) };
    if (body) opts.body = JSON.stringify(body);
    var res  = await fetch(_BASE_API + endpoint, opts);
    var data = await res.json();
    if (!res.ok) {
      // FastAPI validation errors (422) come back as:
      //   { "detail": [{ "loc": [...], "msg": "Weak password", "type": "value_error" }] }
      // Naively using data.detail passes an array to toast() which renders as "[object Object]".
      // We parse it into a readable string here so callers never have to think about this.
      var raw = data.detail || data.message || data.error || ('Request failed (' + res.status + ')');
      var errorMsg;
      if (Array.isArray(raw)) {
        // Join each validation error's human-readable message
        errorMsg = raw.map(function (e) {
          var field = e.loc ? e.loc[e.loc.length - 1] : '';
          return field ? (field + ': ' + e.msg) : e.msg;
        }).join(' · ');
      } else if (typeof raw === 'object') {
        errorMsg = JSON.stringify(raw);
      } else {
        errorMsg = String(raw);
      }
      return { ok: false, error: errorMsg };
    }
    return { ok: true, data: data };
  } catch (err) {
    // Network down, server unreachable, or non-JSON response body
    return { ok: false, error: 'Network error. Check your connection.' };
  }
}

function _adminRequest(method, endpoint, body) {
  return _request(method, endpoint, body, true);
}


// ═══════════════════════════════════════════════════════════════════════════════
//  AUTH — USER
// ═══════════════════════════════════════════════════════════════════════════════

// ── getCurrentUser (SYNC) ─────────────────────────────────────────────────────
// Called from every page's auth guard at the top. Must be synchronous.
// Returns the cached user object, or null if not logged in.
function getCurrentUser() {
  var token = _C.get(_CK.USER_TOKEN)
  var user = _C.get(_CK.USER)
  if (!token) return null;
  return user;
}

// ── loginUser (ASYNC) ─────────────────────────────────────────────────────────
async function loginUser(studentId, password) {
  var res = await _request('POST', _R.user_login, { studentId: studentId, password: password });
  if (!res.ok){
    toast('Registration failed: ' + res.error, 'error');
    return { ok: false, error: res.error };};
if (!res.data){
    toast('Registration failed: ' + res.error, 'error');
    return { ok: false, error: res.error };
  }
  var token = res.data.token;
  var user  = res.data.user;
  _C.set(_CK.USER_TOKEN, token);
  _C.set(_CK.USER,user)
  console.log(user)

  // Pre-populate cache so all subsequent sync reads on other pages work
  await _prefetchForUser(user.id);

  return { ok: true, user: user };
}

// ── registerUser (ASYNC) ──────────────────────────────────────────────────────
async function registerUser(payload) {
  var res = await _request('POST', _R.user_signup, payload);
  console.log('registerUser response:', res);
  if (!res.ok) {
    toast('Registration failed: ' + res.error, 'error');
    return { ok: false, error: res.error };}
  if (!res.data){
    toast('Registration failed: ' + res.error, 'error');
    return { ok: false, error: res.error };
  }
  var token = res.data.token;
  var user  = res.data.user;
  if(!token || !user){
    toast('Registration failed: ' + res.error, 'error');
    return { ok: false, error: res.error };
  }
  _C.set(_CK.USER_TOKEN, token);
  _C.set(_CK.USER,user)
  console.log(user)

  await _prefetchForUser(user.id);

  return { ok: true, user: user };
}

// ── logoutUser (SYNC) ─────────────────────────────────────────────────────────
function logoutUser() {
  _C.del(_CK.USER_TOKEN);
  _C.del(_CK.USER);
  _C.del(_CK.VOTES);
  _C.del(_CK.ACTIVITY);
  // Keep elections + stats cached — they're public data
}

async function refreshUserProfile() {
  var res = await _request('GET', _R.user_me);
  if (!res.ok) {
    return { ok: false, error: res.error };}
  if (!res.data){
    return { ok: false, error: res.error };
  }
  var token = res.data.token;
  var user  = res.data;
  if(!token || !user){
    return { ok: false, error: res.error };
  }
  
  _C.set(_CK.USER_TOKEN, token);
  _C.set(_CK.USER,user)
  console.log("POSTED")

  return null;
}

// Update your prefetch


// ═══════════════════════════════════════════════════════════════════════════════
//  AUTH — ADMIN
// ═══════════════════════════════════════════════════════════════════════════════

// ── isAdmin (SYNC) ────────────────────────────────────────────────────────────
function isAdmin() {
  return !!_C.get(_CK.ADMIN_TOKEN);
}

// ── adminLogin (ASYNC) ────────────────────────────────────────────────────────
async function adminLogin(adminId, password) {
  var res = await _request('POST', _R.admin_login, { adminId: adminId, password: password });
  if (!res.ok) return false;
  _C.set(_CK.ADMIN_TOKEN, res.data.token);
  // Pre-fetch elections and stats so admin-dashboard's sync render() works
  await _fetchAndCacheElections();
  return true;
}

// ── adminLogout ───────────────────────────────────────────────────────────────
function adminLogout() {
  _C.del(_CK.ADMIN_TOKEN);
}
// Alias referenced by admin-dashboard.html
function doAdminLogout_fn() {
  adminLogout();
  window.location.href = './admin-login.html';
}


// ═══════════════════════════════════════════════════════════════════════════════
//  ELECTIONS
//  getElections() uses a cache-first pattern:
//    • If cache is warm → return array immediately (works for sync AND await callers)
//    • If cache is cold → return Promise (only async callers handle this correctly,
//      which is fine because cold cache only happens before login, at which point
//      no page should need elections data yet)
// ═══════════════════════════════════════════════════════════════════════════════

// Internal: fetch elections from API, update cache, pre-fetch stats
async function _fetchAndCacheElections() {

  var res = await _request('GET', _R.elections_all);
  if (!res.ok) {
    toast('Failed to load elections: ' + res.error, 'error');
    return _C.get(_CK.ELECTIONS) || [];
}
  var elections = [];
  if (Array.isArray(res.data)) {
      elections = res.data;
  } else if (res.data && res.data.elections) {
      elections = res.data.elections;
  }

  // Pre-fetch stats for every non-draft election in parallel
  var targets = elections.filter(function (e) {
    return e.status === 'active' || e.status === 'closed';
  });
  if (targets.length > 0) {
    await Promise.allSettled(targets.map(function (e) {
      return _fetchAndCacheStats(e.id);
    }));
  }
  console.log(elections)
  _C.set(_CK.ELECTIONS,elections)
  return elections;
}

// Internal: fetch stats for one election and merge into the stats cache
async function _fetchAndCacheStats(electionId) {
  var res = await _request('GET', _R.stats(electionId));
  if (!res.ok) return;
  var stats = _C.get(_CK.STATS) || {};
  stats[electionId] = res.data;
  _C.set(_CK.STATS, stats);
}

// ── getElections (cache-first) ────────────────────────────────────────────────
function getElections() {
  var cached = _C.get(_CK.ELECTIONS);
  if (cached) {
    // Return cache immediately; refresh in background
    _fetchAndCacheElections();
    return cached;         // plain array — await on this still works: await [] === []
  }
  return _fetchAndCacheElections();  // returns Promise for first cold load
}

// ── getElectionById (SYNC) ────────────────────────────────────────────────────
// Used by voting.html synchronously. Works because elections are cached on login.
function getElectionById(id) {
  var elections = _C.get(_CK.ELECTIONS) || [];
  return elections.find(function (e) { return e.id === id; }) || null;
}

// ── createElection (ASYNC — admin only) ───────────────────────────────────────
async function createElection(data) {
  var res = await _adminRequest('POST', _R.election_create, data);
  if (!res.ok) return { ok: false, error: res.error };
  await _fetchAndCacheElections();   // refresh cache after write
  return { ok: true, election: res.data.election || res.data };
}

// ── updateElection (ASYNC — admin only) ───────────────────────────────────────
async function updateElection(id, updates) {
  var res = await _adminRequest('PUT', _R.election_update(id), updates);
  if (!res.ok) return { ok: false, error: res.error };
  await _fetchAndCacheElections();
  return { ok: true };
}

// ── deleteElection (ASYNC — admin only) ───────────────────────────────────────
async function deleteElection(id) {
  var res = await _adminRequest('DELETE', _R.election_delete(id));
  if (res.ok) await _fetchAndCacheElections();
  return res.ok;
}


// ═══════════════════════════════════════════════════════════════════════════════
//  VOTES
//  Vote cache format: { "elId__posIdx": candidateIndex }
//  This is the same key format the old app.js used, so any code reading
//  the cache directly still works.
// ═══════════════════════════════════════════════════════════════════════════════

// Internal: fetch all votes for a user and populate cache
async function _fetchAndCacheVotes(studentId) {
  var res = await _request('GET', _R.votes_by_user(studentId));
  if (!res.ok) return;

  var votes    = Array.isArray(res.data) ? res.data : (res.data.votes || []);
  var voteMap  = {};
  votes.forEach(function (v) {
    var key = v.electionId + '__' + v.positionIndex;
    voteMap[key] = v.candidateIndex;
  });

  // Wrap in userId key to match getAllVotes() format
  var all  = _C.get(_CK.VOTES) || {};
  all[studentId] = voteMap;
  _C.set(_CK.VOTES, all);
}

// ── getUserVotes (returns vote map for one user, SYNC from cache) ─────────────
function getUserVotes(userId) {
  var all = _C.get(_CK.VOTES) || {};
  return all[userId] || {};
}

// ── getAllVotes (SYNC) ─────────────────────────────────────────────────────────
// Kept for backward compat — admin-dashboard exportData() calls this.
function getAllVotes() {
  return _C.get(_CK.VOTES) || {};
}

// ── hasVotedInElection (SYNC) ─────────────────────────────────────────────────
function hasVotedInElection(userId, electionId) {
  var uv = getUserVotes(userId);
  return Object.keys(uv).some(function (k) {
    return k.indexOf(electionId + '__') === 0;
  });
}

// ── getVoteForPosition (SYNC) ─────────────────────────────────────────────────
function getVoteForPosition(userId, electionId, positionIndex) {
  var uv  = getUserVotes(userId);
  var key = electionId + '__' + positionIndex;
  return (uv[key] !== undefined) ? uv[key] : null;
}

// ── castVote (ASYNC — optimistic update) ─────────────────────────────────────
// Called from voting.html as fire-and-forget. We update the cache immediately
// (optimistic) so the UI reflects the vote right away, then send to the API.
async function castVote(userId, electionId, positionIndex, candidateIndex) {
  // Optimistic: update local cache now so render() shows ✔ Voted instantly
  var all = _C.get(_CK.VOTES) || {};
  if (!all[userId]) all[userId] = {};
  all[userId][electionId + '__' + positionIndex] = candidateIndex;
  _C.set(_CK.VOTES, all);

  // Log activity locally (pre-resolved names for profile.html)
  var election  = getElectionById(electionId);
  var pos       = election ? election.positions[positionIndex] : null;
  var candidate = pos ? pos.candidates[candidateIndex] : null;
  logActivity(userId, {
    type:           'vote',
    electionId:     electionId,
    electionName:   election ? (election.shortName || election.title) : '',
    positionIndex:  positionIndex,
    positionTitle:  pos ? pos.title : '',
    candidateIndex: candidateIndex,
    candidateName:  candidate ? candidate.name : '',
    timestamp:      Date.now()
  });

  // Fire API call in background — the unique constraint on the backend is the
  // real integrity guard; this just persists the vote server-side.
  var res = await _request('POST', _R.vote_cast, {
    userId:         userId,
    electionId:     electionId,
    positionIndex:  positionIndex,
    candidateIndex: candidateIndex
  });

  if (!res.ok && res.error !== 'already_voted') {
    // Silently log — the UI has already advanced so we don't interrupt the user
    console.warn('[castVote] API error:', res.error);
  }

  return res.ok;
}


// ═══════════════════════════════════════════════════════════════════════════════
//  STATS / TALLY
// ═══════════════════════════════════════════════════════════════════════════════

// ── tallyPosition (SYNC from stats cache) ─────────────────────────────────────
// results.html and dashboard.html call this synchronously.
// Stats are pre-fetched inside _fetchAndCacheElections() so the cache is warm.
function tallyPosition(electionId, positionIndex, candidateCount) {
  var fallback = [];
  for (var i = 0; i < candidateCount; i++) {
    fallback.push({ index: i, votes: 0, pct: 0 });
  }

  var statsCache = _C.get(_CK.STATS);
  if (!statsCache || !statsCache[electionId]) return fallback;

  var elStats   = statsCache[electionId];
  var positions = elStats.positions;
  if (!positions || !positions[positionIndex]) return fallback;

  var posData = positions[positionIndex];
  // posData.candidates: [{ candidateIndex, votes, pct }]
  return fallback.map(function (slot, i) {
    var found = (posData.candidates || []).find(function (c) {
      return c.candidateIndex === i;
    }) || { votes: 0, pct: 0 };
    return { index: i, votes: found.votes, pct: found.pct };
  });
}

// ── getTotalVotesCast (SYNC from stats cache) ─────────────────────────────────
// results.html's setInterval calls this without await — must be sync.
function getTotalVotesCast() {
  var statsCache = _C.get(_CK.STATS);
  if (!statsCache) return 0;
  return Object.values(statsCache).reduce(function (sum, s) {
    return sum + (s.totalVotes || 0);
  }, 0);
}

// ── getRegisteredCount (SYNC from cache or overview endpoint) ─────────────────
function getRegisteredCount() {
  return _C.get(_CK.REGISTERED) || 0;
}


// ═══════════════════════════════════════════════════════════════════════════════
//  ACTIVITY LOG
//  Stored locally in localStorage for now.
//  When the backend /activity endpoint is ready, replace the localStorage
//  reads/writes with _request calls (the function signatures stay the same).
// ═══════════════════════════════════════════════════════════════════════════════

function logActivity(userId, item) {
  var all = _C.get(_CK.ACTIVITY) || {};
  if (!all[userId]) all[userId] = [];
  all[userId].unshift(item);
  if (all[userId].length > 50) all[userId] = all[userId].slice(0, 50);
  _C.set(_CK.ACTIVITY, all);
}

function getActivity(userId) {
  var all = _C.get(_CK.ACTIVITY) || {};
  return all[userId] || [];
}


// ═══════════════════════════════════════════════════════════════════════════════
//  LEGACY STUBS
//  Functions called from old code that has no API equivalent yet.
//  They return safe empty values so pages don't crash.
// ═══════════════════════════════════════════════════════════════════════════════

// getUsers() — called by admin-dashboard exportData(). No get-all-users endpoint yet.
function getUsers() { return {}; }


// ═══════════════════════════════════════════════════════════════════════════════
//  PREFETCH HELPERS
//  Called after login to warm up the cache before the user navigates anywhere.
// ═══════════════════════════════════════════════════════════════════════════════

async function _prefetchForUser(studentId) {
  await Promise.allSettled([
    refreshUserProfile(), // Added here
    _fetchAndCacheElections(),
    _fetchAndCacheVotes(studentId),
    _fetchOverview()
  ]);
}

async function _fetchOverview() {
  var res = await _request('GET', _R.stats_overview);
  if (res.ok && res.data.registeredStudents !== undefined) {
    _C.set(_CK.REGISTERED, res.data.registeredStudents);
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
//  PAGE-LEVEL HANDLERS
//  These are defined globally so onclick="doLogin()" etc. work.
//  Previously these lived inside <script type="module"> blocks, making them
//  invisible to HTML onclick attributes (module scope ≠ global scope).
// ═══════════════════════════════════════════════════════════════════════════════

// ── index.html ────────────────────────────────────────────────────────────────
async function doLogin() {
  var id = document.getElementById('login-id').value.trim();
  var pw = document.getElementById('login-pw').value.trim();
  if (!id || !pw) { toast('Please fill in all fields', 'error'); return; }

  toast('Signing in…', '');
  var result = await loginUser(id, pw);
  if (!result.ok) { toast(result.error, 'error'); return; }

  toast('Welcome back, ' + result.user.name + ' 👋', 'success');
  setTimeout(function () { window.location.href = 'pages/user/dashboard.html'; }, 800);
}

// ── register.html ─────────────────────────────────────────────────────────────
async function doRegister() {
  var name   = document.getElementById('reg-name').value.trim();
  var id     = document.getElementById('reg-id').value.trim();
  var index  = document.getElementById('reg-index').value.trim();
  var course = document.getElementById('reg-course').value;
  var pw     = document.getElementById('reg-pw').value.trim();
  var pw2    = document.getElementById('reg-pw2').value.trim();

  if (!name || !id || !index || !course || !pw || !pw2) {
    toast('Please fill in all fields', 'error'); return;
  }
  if (pw !== pw2) { toast('Passwords do not match', 'error'); return; }

  toast('Creating your account…', '');
  var result = await registerUser({ name: name, id: id, index: index, course: course, password: pw });
  if (!result.ok) { toast(result.error, 'error'); return; }

  toast('Account created! 🎉', 'success');
  setTimeout(function () { window.location.href = './dashboard.html'; }, 800);
  location.reload();  // ensure cache is fresh for dashboard
}

// ── admin-login.html ──────────────────────────────────────────────────────────
async function doAdminLogin() {
  var id = document.getElementById('admin-id').value.trim();
  var pw = document.getElementById('admin-pw').value.trim();
  if (!id || !pw) { toast('Please enter admin credentials', 'error'); return; }

  toast('Verifying…', '');
  var ok = await adminLogin(id, pw);
  if (ok) {
    toast('Admin access granted ✅', 'success');
    setTimeout(function () { window.location.href = './admin-dashboard.html'; }, 800);
  } else {
    toast('Invalid credentials', 'error');
  }
}

// ── admin-dashboard.html ──────────────────────────────────────────────────────
function doAdminLogout() {
  doAdminLogout_fn();
}

// ── profile.html ──────────────────────────────────────────────────────────────
function doLogout() {
  logoutUser();
  toast('Logged out successfully');
  setTimeout(function () { window.location.href = '../../index.html'; }, 600);
}

// ── create-election.html (async save) ─────────────────────────────────────────
// The original saveElection() called createElection/updateElection synchronously.
// We redefine it here as async. The HTML button calls saveElection() which now
// properly awaits the API response before navigating.
async function saveElection() {
  var title     = document.getElementById('el-title').value.trim();
  var shortName = document.getElementById('el-short').value.trim() || title;
  var category  = document.getElementById('el-category').value;
  var status    = document.getElementById('el-status').value;
  var startDate = document.getElementById('el-start-date').value;
  var startTime = document.getElementById('el-start-time').value;
  var endDate   = document.getElementById('el-end-date').value;
  var endTime   = document.getElementById('el-end-time').value;

  if (!title)     { toast('Please enter an election title', 'error'); return; }
  if (!category)  { toast('Please select a category', 'error'); return; }
  if (!startDate) { toast('Please set a start date', 'error'); return; }
  if (!endDate)   { toast('Please set an end date', 'error'); return; }

  // collectPositions() is defined in create-election.html's inline script
  var positions = (typeof collectPositions === 'function') ? collectPositions() : [];
  if (positions.length === 0) {
    toast('Add at least one position with a candidate', 'error'); return;
  }

  var data = {
    title: title, shortName: shortName, category: category, status: status,
    startDate: startDate, startTime: startTime, endDate: endDate, endTime: endTime,
    positions: positions
  };

  // editId and editElection are set by create-election.html's inline script
  var editId = (typeof window.editId !== 'undefined') ? window.editId : null;

  toast('Saving…', '');
  var result;
  if (editId) {
    result = await updateElection(editId, data);
    if (result.ok) toast('"' + title + '" updated ✅', 'success');
    else           toast(result.error || 'Update failed', 'error');
  } else {
    result = await createElection(data);
    if (result.ok) toast('"' + title + '" created with ' + positions.length + ' position(s)! 🎉', 'success');
    else           toast(result.error || 'Create failed', 'error');
  }

  if (result.ok) {
    setTimeout(function () { window.location.href = './admin-dashboard.html'; }, 900);
  }
}

// ── admin-dashboard.html confirmDel() ─────────────────────────────────────────
async function confirmDel(id, title) {
  if (!confirm('Delete "' + title + '"? This cannot be undone.')) return;
  var ok = await deleteElection(id);
  if (ok) {
    toast('"' + title + '" deleted', 'error');
    // render() is defined in admin-dashboard.html's inline script
    if (typeof render === 'function') render();
  } else {
    toast('Delete failed', 'error');
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
//  STARTUP — warm the cache if a session already exists
//  This runs on every page load. If the user is already logged in (token in
//  localStorage from a previous session), pre-fetch elections and votes so
//  sync reads on the current page work without waiting for explicit API calls.
// ═══════════════════════════════════════════════════════════════════════════════

(async function _startup() {
  var userToken  = _C.get(_CK.USER_TOKEN);
  var adminToken = _C.get(_CK.ADMIN_TOKEN);

  if (!userToken && !adminToken) return console.log("not logged in");  // not logged in, nothing to warm

  // Elections + stats are needed by everyone
  if (!_C.get(_CK.ELECTIONS)) {
    await _fetchAndCacheElections();
  }

  // User votes are needed for hasVotedInElection / getVoteForPosition
  if (userToken) {
    var user = _C.get(_CK.USER);
    if (user && user.id && !_C.get(_CK.VOTES)) {
      await _fetchAndCacheVotes(user.id);
    }
  }

  // Registered count for admin dashboard
  if (adminToken && !_C.get(_CK.REGISTERED)) {
    await _fetchOverview();
  }
}());