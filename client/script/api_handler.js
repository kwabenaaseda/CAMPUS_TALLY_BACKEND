/* ═══════════════════════════════════════════════════════════════
   CAMPUSTALLY — API Handler
   ═══════════════════════════════════════════════════════════════

   This module replaces app.js's localStorage data layer with
   real HTTP calls to the backend API.

   It mirrors every public function from app.js so the HTML pages
   only need minimal changes (async/await + import swap).

   Import pattern in HTML pages:
   ─────────────────────────────────────────────────────────────
   <script >
     import { loginUser, getElections, ... } from '../../script/api_handler.js';
     // your page logic here (must be async where needed)
   </script>
   ═══════════════════════════════════════════════════════════════ */

import { baseAPI } from './env.js';
import API         from './route.js';


// ───────────────────────────────────────────────────────────────
//  TOKEN STORE
//  After login the backend returns a JWT. We keep it in
//  localStorage so the user stays logged in across page loads.
// ───────────────────────────────────────────────────────────────
const Token = {
  USER_KEY:  'ct_token',
  ADMIN_KEY: 'ct_admin_token',

  getUser()       { return localStorage.getItem(Token.USER_KEY); },
  setUser(t)      { localStorage.setItem(Token.USER_KEY, t); },
  delUser()       { localStorage.removeItem(Token.USER_KEY); },

  getAdmin()      { return localStorage.getItem(Token.ADMIN_KEY); },
  setAdmin(t)     { localStorage.setItem(Token.ADMIN_KEY, t); },
  delAdmin()      { localStorage.removeItem(Token.ADMIN_KEY); },

  // Build an Authorization header for authenticated requests
  userHeaders() {
    const t = Token.getUser();
    return {
      'Content-Type': 'application/json',
      ...(t ? { Authorization: 'Bearer ' + t } : {})
    };
  },

  adminHeaders() {
    const t = Token.getAdmin();
    return {
      'Content-Type': 'application/json',
      ...(t ? { Authorization: 'Bearer ' + t } : {})
    };
  }
};


// ───────────────────────────────────────────────────────────────
//  USER CACHE
//  We cache the logged-in user object so that getCurrentUser()
//  can stay SYNCHRONOUS (needed by auth guards on every page
//  before any async work begins).
// ───────────────────────────────────────────────────────────────
const UserCache = {
  KEY: 'ct_user',
  get()     { try { return JSON.parse(localStorage.getItem(UserCache.KEY)); } catch { return null; } },
  set(user) { localStorage.setItem(UserCache.KEY, JSON.stringify(user)); },
  del()     { localStorage.removeItem(UserCache.KEY); }
};


// ───────────────────────────────────────────────────────────────
//  CORE FETCH WRAPPERS
//  All HTTP calls go through these two helpers.
//  They always return: { ok: true, data } | { ok: false, error }
//  so callers never have to think about HTTP status codes.
// ───────────────────────────────────────────────────────────────
async function request(method, endpoint, body = null, headers = Token.userHeaders()) {
  try {
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const res  = await fetch(baseAPI + endpoint, opts);
    const data = await res.json();

    if (!res.ok) {
      return { ok: false, error: data.message || data.error || `Request failed (${res.status})` };
    }
    return { ok: true, data };

  } catch (err) {
    // Network failure, server down, JSON parse error, etc.
    return { ok: false, error: 'Network error. Please check your connection.' };
  }
}

// Shorthand for admin calls — uses the admin token header
function adminRequest(method, endpoint, body = null) {
  return request(method, endpoint, body, Token.adminHeaders());
}


// ═══════════════════════════════════════════════════════════════
//  AUTH — USER
// ═══════════════════════════════════════════════════════════════

/**
 * Register a new student account.
 * @param {{ name, id, index, course, password }} payload
 * @returns {{ ok, user?, error? }}
 */
async function registerUser(payload) {
  const res = await request('POST', API.user_signup, payload);
  if (!res.ok) return { ok: false, error: res.error };

  // Backend should return: { token, user }
  const { token, user } = res.data;
  Token.setUser(token);
  UserCache.set(user);
  return { ok: true, user };
}

/**
 * Log in an existing student.
 * @param {string} studentId
 * @param {string} password
 * @returns {{ ok, user?, error? }}
 */
/* async function loginUser(studentId, password) {
  const res = await request('POST', API.user_login, { studentId, password });
  if (!res.ok) return { ok: false, error: res.error };

  const { token, user } = res.data;
  Token.setUser(token);
  UserCache.set(user);
  return { ok: true, user };
} */

/**
 * Returns the currently logged-in user from cache (SYNCHRONOUS).
 * This mirrors the old app.js getCurrentUser() exactly so that
 * auth guards at the top of every page still work without await.
 * @returns {object|null}
 */
/* function getCurrentUser() {
  if (!Token.getUser()) return null; // token gone = logged out
  return UserCache.get();
} */

/**
 * Log out: wipe token and user cache.
 */
function logoutUser() {
  Token.delUser();
  UserCache.del();
}


// ═══════════════════════════════════════════════════════════════
//  AUTH — ADMIN
// ═══════════════════════════════════════════════════════════════

/**
 * Admin login.
 * @param {string} adminId
 * @param {string} password
 * @returns {boolean}
 */
async function adminLogin(adminId, password) {
  const res = await request('POST', API.admin_login, { adminId, password });
  if (!res.ok) return false;
  Token.setAdmin(res.data.token);
  return true;
}

/**
 * Check if an admin session is active (SYNCHRONOUS).
 * Mirrors old app.js isAdmin() so admin page guards still work.
 * @returns {boolean}
 */
function isAdmin() {
  return !!Token.getAdmin();
}

/**
 * Admin logout.
 */
function adminLogout() {
  Token.delAdmin();
}


// ═══════════════════════════════════════════════════════════════
//  ELECTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Fetch all elections visible to the current user.
 * @returns {ElectionObject[]}
 */
async function getElections() {
  const res = await request('GET', API.admin_get_elections);
  if (!res.ok) return [];
  // Backend may wrap in { elections: [...] } or return array directly
  return Array.isArray(res.data) ? res.data : (res.data.elections ?? []);
}

/**
 * Fetch a single election by ID.
 * @param {string} id
 * @returns {ElectionObject|null}
 */
async function getElectionById(id) {
  const res = await request('GET', API.admin_get_election(id));
  if (!res.ok) return null;
  return res.data.election ?? res.data;
}

/**
 * Create a new election (admin only).
 * @param {object} data
 * @returns {{ ok, election?, error? }}
 */
async function createElection(data) {
  const res = await adminRequest('POST', API.admin_create_election, data);
  if (!res.ok) return { ok: false, error: res.error };
  return { ok: true, election: res.data.election ?? res.data };
}

/**
 * Update an existing election (admin only).
 * @param {string} id
 * @param {object} updates
 * @returns {{ ok, error? }}
 */
async function updateElection(id, updates) {
  const res = await adminRequest('PUT', API.admin_update_election(id), updates);
  if (!res.ok) return { ok: false, error: res.error };
  return { ok: true };
}

/**
 * Delete an election (admin only).
 * @param {string} id
 * @returns {boolean}
 */
async function deleteElection(id) {
  const res = await adminRequest('DELETE', API.admin_delete_election(id));
  return res.ok;
}


// ═══════════════════════════════════════════════════════════════
//  VOTES
// ═══════════════════════════════════════════════════════════════

/**
 * Cast a vote for a candidate.
 * @param {string} userId
 * @param {string} electionId
 * @param {number} positionIndex
 * @param {number} candidateIndex
 * @returns {boolean}  true = success
 */
async function castVote(userId, electionId, positionIndex, candidateIndex) {
  const res = await request('POST', API.user_vote, {
    userId,
    electionId,
    positionIndex,
    candidateIndex
  });
  return res.ok;
}

/**
 * Fetch all votes cast by a specific user.
 * Used to drive hasVotedInElection and getVoteForPosition.
 * @param {string} userId
 * @returns {VoteRecord[]}
 *   Each record: { electionId, positionIndex, candidateIndex, timestamp }
 */
async function getUserVotes(userId) {
  const res = await request('GET', API.user_get_vote_by_user(userId));
  if (!res.ok) return [];
  return Array.isArray(res.data) ? res.data : (res.data.votes ?? []);
}

/**
 * Check whether a user has voted in a given election.
 * @param {string} userId
 * @param {string} electionId
 * @returns {boolean}
 */
async function hasVotedInElection(userId, electionId) {
  const votes = await getUserVotes(userId);
  return votes.some(v => v.electionId === electionId);
}

/**
 * Get the candidateIndex a user voted for in a specific position.
 * Returns null if they haven't voted for that position yet.
 * @param {string} userId
 * @param {string} electionId
 * @param {number} positionIndex
 * @returns {number|null}
 */
async function getVoteForPosition(userId, electionId, positionIndex) {
  const votes = await getUserVotes(userId);
  const match = votes.find(
    v => v.electionId === electionId && v.positionIndex === positionIndex
  );
  return match !== undefined ? match.candidateIndex : null;
}

/**
 * Get all votes cast across all elections (admin overview).
 * @param {string} electionId
 * @returns {VoteRecord[]}
 */
async function getVotesByElection(electionId) {
  const res = await request('GET', API.all_get_votes_by_election(electionId));
  if (!res.ok) return [];
  return Array.isArray(res.data) ? res.data : (res.data.votes ?? []);
}


// ═══════════════════════════════════════════════════════════════
//  STATS / TALLY
// ═══════════════════════════════════════════════════════════════

/**
 * Tally results for one position in an election.
 * Returns an array indexed by candidate, shaped the same way
 * the old localStorage tallyPosition() was — so results.html
 * and dashboard.html don't need restructuring.
 *
 * Expected backend shape for GET /stats/election/:id:
 * {
 *   positions: [
 *     [ { candidateIndex: 0, votes: 240 }, { candidateIndex: 1, votes: 180 } ],
 *     ...
 *   ]
 * }
 *
 * @param {string} electionId
 * @param {number} positionIndex
 * @param {number} candidateCount
 * @returns {{ index, votes, pct }[]}
 */
async function tallyPosition(electionId, positionIndex, candidateCount) {
  const fallback = Array.from({ length: candidateCount }, (_, i) => ({
    index: i, votes: 0, pct: 0
  }));

  const res = await request('GET', API.all_get_stats(electionId));
  if (!res.ok) return fallback;

  const positions = res.data.positions;
  if (!Array.isArray(positions) || !positions[positionIndex]) return fallback;

  const posData = positions[positionIndex]; // array of { candidateIndex, votes }
  const total   = posData.reduce((s, c) => s + (c.votes ?? 0), 0);

  // Rebuild as an array indexed 0..candidateCount-1
  return Array.from({ length: candidateCount }, (_, i) => {
    const found = posData.find(c => c.candidateIndex === i) ?? { votes: 0 };
    return {
      index: i,
      votes: found.votes,
      pct:   total > 0 ? Math.round((found.votes / total) * 100) : 0
    };
  });
}

/**
 * Get the total number of votes cast across all elections.
 * Used by results.html and admin-dashboard.html.
 * @returns {number}
 */
async function getTotalVotesCast() {
  const elections = await getElections();
  let total = 0;
  // Fire all stats requests in parallel — much faster than sequential awaits
  const results = await Promise.allSettled(
    elections.map(el => request('GET', API.all_get_stats(el.id)))
  );
  results.forEach(r => {
    if (r.status === 'fulfilled' && r.value.ok) {
      total += r.value.data.totalVotes ?? 0;
    }
  });
  return total;
}

/**
 * Get number of registered students.
 * NOTE: This endpoint isn't in route.js yet — add it when the
 * backend exposes it. Returns 0 safely in the meantime.
 * @returns {number}
 */
async function getRegisteredCount() {
  // TODO: add API.all_get_registered_count to route.js when available
  // const res = await request('GET', '/stats/registered');
  // return res.ok ? (res.data.count ?? 0) : 0;
  return 0;
}


// ═══════════════════════════════════════════════════════════════
//  ACTIVITY LOG
//  The old app.js stored activity locally. With a real backend
//  activity should be server-side. These stubs keep the UI
//  working while the endpoint is built out.
// ═══════════════════════════════════════════════════════════════

/**
 * Log a user activity event.
 * Falls back to localStorage so the UI doesn't break before
 * the backend activity endpoint is ready.
 * @param {string} userId
 * @param {object} item
 */
function logActivity(userId, item) {
  // TODO: replace with POST /activity when backend is ready
  // await request('POST', '/activity', { userId, ...item });

  // Temporary localStorage fallback
  const KEY = 'ct_activity';
  try {
    const all = JSON.parse(localStorage.getItem(KEY)) || {};
    if (!all[userId]) all[userId] = [];
    all[userId].unshift(item);
    if (all[userId].length > 50) all[userId] = all[userId].slice(0, 50);
    localStorage.setItem(KEY, JSON.stringify(all));
  } catch { /* silent fail */ }
}

/**
 * Fetch activity for a user (from localStorage fallback for now).
 * @param {string} userId
 * @returns {ActivityItem[]}
 */
function getActivity(userId) {
  // TODO: replace with GET /activity/:userId when backend is ready
  try {
    const all = JSON.parse(localStorage.getItem('ct_activity')) || {};
    return all[userId] ?? [];
  } catch { return []; }
}


// ═══════════════════════════════════════════════════════════════
//  UI UTILITIES  (kept here so pages only need one import)
// ═══════════════════════════════════════════════════════════════

function toast(msg, type = '') {
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
  setTimeout(() => el.remove(), 3200);
}

function togglePw(inputId, btn) {
  const inp = document.getElementById(inputId);
  inp.type    = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁️' : '🙈';
}

function fmtTime(ts) {
  return new Date(ts).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit', hour12: true
  });
}

function startCountdown(elementId, hours) {
  const el = document.getElementById(elementId);
  if (!el) return;
  let seconds = hours * 3600;
  function tick() {
    seconds = Math.max(0, seconds - 1);
    const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
    const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    el.textContent = `${h}:${m}:${s}`;
  }
  tick();
  setInterval(tick, 1000);
}


// ═══════════════════════════════════════════════════════════════
//  EXPORTS
// ═══════════════════════════════════════════════════════════════
export {
  // Auth
  registerUser, loginUser, getCurrentUser, logoutUser,

  // Admin
  adminLogin, isAdmin, adminLogout,

  // Elections
  getElections, getElectionById, createElection, updateElection, deleteElection,

  // Votes
  castVote, getUserVotes, hasVotedInElection, getVoteForPosition, getVotesByElection,

  // Stats
  tallyPosition, getTotalVotesCast, getRegisteredCount,

  // Activity
  logActivity, getActivity,

  // UI utilities
  toast, togglePw, fmtTime, startCountdown
};