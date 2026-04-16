/* ======================================================
   AI Trading Assistant  –  app.js
   Tabs: Intraday | Wishlist | AI Chat
   ====================================================== */

"use strict";

// ── Cognito Auth Config ───────────────────────────────────────────────────────
// Fill these in after running: terraform output cognito_user_pool_id / cognito_client_id
const COGNITO_USER_POOL_ID = "us-east-1_N9lSioH0J";
const COGNITO_CLIENT_ID    = "41go0jefn91jvgg2hsitbu3f79";

const _userPool = new AmazonCognitoIdentity.CognitoUserPool({
  UserPoolId: COGNITO_USER_POOL_ID,
  ClientId:   COGNITO_CLIENT_ID,
});
let _cognitoUser     = null;
let _pendingEmail    = "";   // stored between signup → confirm steps

// ── Authenticated fetch wrapper ───────────────────────────────────────────────
// Intercepts every /api/* call and injects the Cognito ID token.
// getSession() auto-refreshes the token when it expires — no extra code needed.
const _origFetch = window.fetch;
window.fetch = function(url, opts) {
  if (typeof url === "string" && url.startsWith("/api/")) {
    return new Promise((resolve, reject) => {
      const user = _userPool.getCurrentUser();
      if (!user) { doLogout(); return reject(new Error("Not authenticated")); }
      user.getSession((err, session) => {
        if (err || !session.isValid()) { doLogout(); return reject(new Error("Session expired")); }
        const token = session.getIdToken().getJwtToken();
        opts = opts || {};
        opts.headers = Object.assign({}, opts.headers || {}, { Authorization: token });
        _origFetch(url, opts)
          .then(resp => { if (resp.status === 401) doLogout(); resolve(resp); })
          .catch(reject);
      });
    });
  }
  return _origFetch(url, opts);
};

// ── Auth UI helpers ───────────────────────────────────────────────────────────
function showAuthUI() {
  document.getElementById("auth-container").style.display = "";
  document.getElementById("app-container").style.display  = "none";
  showAuthForm("form-login");
}

function showAuthForm(id) {
  ["form-login", "form-signup", "form-confirm"].forEach(f => {
    document.getElementById(f).classList.add("d-none");
  });
  document.getElementById(id).classList.remove("d-none");
  document.getElementById("auth-error").classList.add("d-none");
  document.getElementById("auth-success").classList.add("d-none");
}

function showAuthError(msg) {
  const el = document.getElementById("auth-error");
  el.textContent = msg;
  el.classList.remove("d-none");
}

function showAuthSuccess(msg) {
  const el = document.getElementById("auth-success");
  el.textContent = msg;
  el.classList.remove("d-none");
}

function _setAuthBtnLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle("auth-btn-loading", loading);
}

function onAuthSuccess(user) {
  _cognitoUser = user;
  // Show the email in the header
  user.getSession((err, session) => {
    if (!err && session) {
      const email = session.getIdToken().payload.email || "";
      const el = document.getElementById("user-email-display");
      if (el) el.textContent = email;
    }
  });
  document.getElementById("auth-container").style.display = "none";
  document.getElementById("app-container").style.display  = "";
  // Boot the app

  // Default: show ALL signals so sector filters always have results
  activeFilter = "ALL";
  document.querySelectorAll(".btn-filter").forEach(function(b) { b.classList.remove("active"); });
  const allBtn = document.querySelector(".btn-filter.all");
  if (allBtn) allBtn.classList.add("active");

  _loadSignalSnapshot();   // load previous signals before first render
  loadStocks(false);
  loadNews();
  loadWishlistCount();
  loadKnownStocks();
  loadIndexData();
  startCountdown();
  document.addEventListener("click", function(e) {
    const wrap = document.querySelector(".wishlist-input-wrap");
    const sugg = document.getElementById("search-suggestions");
    if (sugg && wrap && !wrap.contains(e.target)) sugg.classList.add("d-none");
  });
}

// ── Login ─────────────────────────────────────────────────────────────────────
function doLogin() {
  const email    = (document.getElementById("login-email").value || "").trim();
  const password = document.getElementById("login-password").value || "";
  if (!email || !password) return showAuthError("Please enter your email and password.");
  _setAuthBtnLoading("login-btn", true);

  const authDetails  = new AmazonCognitoIdentity.AuthenticationDetails({ Username: email, Password: password });
  const cognitoUser  = new AmazonCognitoIdentity.CognitoUser({ Username: email, Pool: _userPool });

  cognitoUser.authenticateUser(authDetails, {
    onSuccess: ()    => onAuthSuccess(cognitoUser),
    onFailure: (err) => { _setAuthBtnLoading("login-btn", false); showAuthError(err.message); },
  });
}

// ── Signup ────────────────────────────────────────────────────────────────────
function doSignup() {
  const email    = (document.getElementById("signup-email").value || "").trim();
  const password = document.getElementById("signup-password").value || "";
  const confirm  = document.getElementById("signup-confirm").value  || "";

  if (!email || !password) return showAuthError("Please fill in all fields.");
  if (password !== confirm) return showAuthError("Passwords do not match.");
  if (password.length < 8)  return showAuthError("Password must be at least 8 characters.");
  _setAuthBtnLoading("signup-btn", true);

  const emailAttr = new AmazonCognitoIdentity.CognitoUserAttribute({ Name: "email", Value: email });

  _userPool.signUp(email, password, [emailAttr], null, (err) => {
    _setAuthBtnLoading("signup-btn", false);
    if (err) return showAuthError(err.message);
    _pendingEmail = email;
    showAuthForm("form-confirm");
    document.getElementById("confirm-email-display").textContent = email;
  });
}

// ── Confirm email ─────────────────────────────────────────────────────────────
function doConfirm() {
  const code = (document.getElementById("confirm-code").value || "").trim();
  if (!code) return showAuthError("Please enter the verification code.");
  _setAuthBtnLoading("confirm-btn", true);

  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({ Username: _pendingEmail, Pool: _userPool });
  cognitoUser.confirmRegistration(code, true, (err) => {
    _setAuthBtnLoading("confirm-btn", false);
    if (err) return showAuthError(err.message);
    showAuthForm("form-login");
    showAuthSuccess("Account confirmed! Please sign in.");
  });
}

// ── Resend verification code ───────────────────────────────────────────────────
function doResendCode() {
  if (!_pendingEmail) return;
  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({ Username: _pendingEmail, Pool: _userPool });
  cognitoUser.resendConfirmationCode((err) => {
    if (err) return showAuthError(err.message);
    showAuthSuccess("Code resent — check your inbox.");
  });
}

// ── Logout ────────────────────────────────────────────────────────────────────
function doLogout() {
  if (_cognitoUser) _cognitoUser.signOut();
  _cognitoUser = null;
  showAuthUI();
}

// ── State ─────────────────────────────────────────────────────────────────────
let allStocks          = [];
let activeFilter       = "ALL";
let activeSector       = "ALL";
let modalChart         = null;
let currentModalData   = null;   // stores last-loaded stock detail for chart TF switching
let wishlistSymbols    = new Set();
let currentModalSymbol = null;
let currentTab         = "intraday";
let countdownTimer     = null;
let countdownSecs      = 300;
let marketIsOpen       = false;   // updated by loadIndexData(); drives refresh interval
let activeSort         = "score"; // score | rr | change | volume
let prevSignals        = {};      // {symbol: signal} snapshot from last load
let knownStocks        = [];
let currentPage        = 1;
const STOCKS_PER_PAGE  = 20;
let backgroundLoadDone = false;
let _bgRefreshInProgress = false;  // true while a background refresh is in-flight

// ── Init — gate on Cognito session ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const user = _userPool.getCurrentUser();
  if (user) {
    user.getSession((err, session) => {
      if (!err && session && session.isValid()) {
        onAuthSuccess(user);
      } else {
        showAuthUI();
      }
    });
  } else {
    showAuthUI();
  }
});

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;

  // Update tab buttons
  document.querySelectorAll(".main-tab-btn").forEach(b => b.classList.remove("active"));
  const btn = document.getElementById("tab-btn-" + tab);
  if (btn) btn.classList.add("active");

  // Show/hide panels
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("d-none"));
  const panel = document.getElementById("tab-" + tab);
  if (panel) panel.classList.remove("d-none");

  // Lazy-load on first switch
  if (tab === "wishlist")             loadWishlist();
  if (tab === "portfolio")            loadPortfolio();
}

function refreshCurrentTab() {
  if (currentTab === "intraday")       loadStocks(true);
  else if (currentTab === "wishlist")  loadWishlist();
  else if (currentTab === "portfolio") loadPortfolio();
}

// ── Autocomplete ──────────────────────────────────────────────────────────────

async function loadKnownStocks() {
  try {
    const r = await fetch("/api/stocks/list");
    if (!r.ok) return;
    const d = await r.json();
    // API returns a plain array; guard against {stocks:[]} shape too
    knownStocks = Array.isArray(d) ? d : (d.stocks || []);
  } catch (_) {}
}

function onSearchInput() {
  const input = document.getElementById("wishlist-input");
  const sugg  = document.getElementById("search-suggestions");
  if (!sugg) return;

  const q = input ? input.value.trim() : "";
  if (!q) { sugg.classList.add("d-none"); return; }

  const qU = q.toUpperCase();
  const matches = knownStocks.filter(function(s) {
    const bare = s.symbol.replace(".NS","").replace(".BO","").toUpperCase();
    return bare.includes(qU) || s.name.toUpperCase().includes(qU);
  }).slice(0, 8);

  if (!matches.length) { sugg.classList.add("d-none"); return; }

  sugg.innerHTML = matches.map(function(s) {
    const ss = s.symbol.replace(/'/g, "\\'");
    const sn = s.name.replace(/'/g, "\\'");
    return '<div class="suggestion-item" onclick="selectSuggestion(\'' + ss + '\',\'' + sn + '\')">'
      + '<span class="suggestion-symbol">' + s.symbol + '</span>'
      + '<span class="suggestion-name">' + s.name + '</span>'
      + '</div>';
  }).join("");
  sugg.classList.remove("d-none");
}

function handleSearchKey(event) {
  const sugg = document.getElementById("search-suggestions");
  if (event.key === "Enter") {
    if (sugg) sugg.classList.add("d-none");
    addToWishlistManual();
  } else if (event.key === "Escape") {
    if (sugg) sugg.classList.add("d-none");
  }
}

function selectSuggestion(symbol, name) {
  const input = document.getElementById("wishlist-input");
  if (input) input.value = symbol;
  const sugg = document.getElementById("search-suggestions");
  if (sugg) sugg.classList.add("d-none");
  addToWishlistManual();
}

// ── Intraday free-form stock search ───────────────────────────────────────────

function onStockSearchInput() {
  const q   = (document.getElementById("stock-search-input").value || "").trim().toUpperCase();
  const box = document.getElementById("stock-search-suggestions");
  if (!q) { box.classList.add("d-none"); return; }

  const matches = knownStocks.filter(function(s) {
    const bare = s.symbol.replace(".NS", "").replace(".BO", "").toUpperCase();
    return bare.includes(q) || s.name.toUpperCase().includes(q);
  }).slice(0, 8);

  if (!matches.length) { box.classList.add("d-none"); return; }

  box.innerHTML = matches.map(function(s) {
    const bare = s.symbol.replace(".NS", "").replace(".BO", "");
    const ss   = bare.replace(/'/g, "\\'");
    return '<div class="suggestion-item" onclick="selectStockSuggestion(\'' + ss + '\')">'
      + '<span class="suggestion-symbol">' + bare + '</span>'
      + '<span class="suggestion-name">' + s.name + '</span>'
      + '</div>';
  }).join("");
  box.classList.remove("d-none");
}

function selectStockSuggestion(bareSymbol) {
  document.getElementById("stock-search-input").value = bareSymbol;
  document.getElementById("stock-search-suggestions").classList.add("d-none");
  analyseCustomStock();
}

async function analyseCustomStock() {
  let sym = (document.getElementById("stock-search-input").value || "").trim().toUpperCase();
  if (!sym) return;
  document.getElementById("stock-search-suggestions").classList.add("d-none");

  // Auto-append .NS if no exchange suffix provided
  if (!sym.endsWith(".NS") && !sym.endsWith(".BO")) sym += ".NS";

  const container = document.getElementById("search-result-container");
  container.style.display = "block";
  container.innerHTML =
    '<div class="text-center py-4">'
    + '<div class="spinner-border text-primary"></div>'
    + '<p class="mt-2 text-muted">Analysing ' + sym + '\u2026</p>'
    + '</div>';

  try {
    // encodeURIComponent handles M&M → M%26M correctly; API Gateway decodes it back
    const r    = await fetch("/api/stock/" + encodeURIComponent(sym));
    const data = await r.json();

    if (data.error || data.unavailable) {
      container.innerHTML =
        '<div class="alert alert-warning">'
        + '\u26a0\ufe0f Could not analyse <strong>' + sym + '</strong>. '
        + (data.error || data.explanation || "No data available on Yahoo Finance.")
        + '</div>';
      return;
    }

    container.innerHTML =
      '<div class="d-flex align-items-center gap-2 mb-2">'
      + '<span class="fw-semibold text-muted">\uD83D\uDD0D Search result</span>'
      + '<button class="btn btn-sm btn-outline-secondary" '
      + 'onclick="document.getElementById(\'search-result-container\').style.display=\'none\'">'
      + '\u2715 Clear</button>'
      + '</div>'
      + stockCard(data, false);

    // Sync wishlist heart state for the result card
    container.querySelectorAll(".btn-heart").forEach(function(btn) {
      if (wishlistSymbols.has(btn.dataset.symbol)) btn.classList.add("active");
    });
  } catch (e) {
    container.innerHTML =
      '<div class="alert alert-danger">Error fetching data for ' + sym + '. Please try again.</div>';
  }
}

// ── Market status ─────────────────────────────────────────────────────────────

// ═══════════════════════════════════════════════════════════════ INTRADAY TAB ═

async function loadStocks(forceRefresh) {
  const hasExistingData = allStocks.length > 0;

  // ── PATH A: Initial load (no data yet) — show full spinner ──────────────
  if (!hasExistingData) {
    if (forceRefresh) {
      await fetch("/api/cache", { method: "DELETE" });
    }

    showEl("loading-section");
    hideEl("error-section");
    hideEl("summary-row");
    hideEl("stocks-section");
    backgroundLoadDone = false;
    currentPage = 1;

    const btn = document.getElementById("refresh-btn");
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading\u2026'; }

    try {
      loadedPages = {};
      const r = await fetch("/api/stocks?page=1&per_page=" + STOCKS_PER_PAGE);
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();

      allStocks = data.stocks || [];
      totalStocksCount = data.total || allStocks.length;
      loadedPages[1] = true;

      renderStocks();
      renderSignalStats();
      _saveSignalSnapshot();
      renderGapScanner();

      hideEl("loading-section");
      showEl("summary-row");
      showEl("stocks-section");

      await loadWishlistSymbols();
      _syncAllHearts();

      _loadRemainingStocks();
    } catch (e) {
      console.error(e);
      hideEl("loading-section");
      showEl("error-section");
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh'; }
    }
    return;
  }

  // ── PATH B: Background refresh (data already visible) ───────────────────
  // Keep existing data on screen while fetching new data silently.
  if (_bgRefreshInProgress) return;  // prevent overlapping refreshes
  _bgRefreshInProgress = true;
  _showUpdateIndicator();

  const btn = document.getElementById("refresh-btn");
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Updating\u2026'; }

  try {
    if (forceRefresh) {
      await fetch("/api/cache", { method: "DELETE" });
    }

    // Fetch page 1 fresh — all 80 cards stay on screen while this loads
    const r = await fetch("/api/stocks?page=1&per_page=" + STOCKS_PER_PAGE);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const data = await r.json();

    const newStocks = data.stocks || [];
    totalStocksCount = data.total || allStocks.length;

    // MERGE into existing array — cards never vanish, only data updates
    _mergeStocks(allStocks, newStocks);

    renderStocks();
    renderSignalStats();
    _saveSignalSnapshot();
    renderGapScanner();

    // M1: Mark pages 2-4 as stale so _loadRemainingStocks re-fetches them
    loadedPages = { 1: true };

    // C1: AWAIT all pages so the _bgRefreshInProgress guard stays true until
    //     every page has finished merging — prevents overlapping refreshes.
    // M2: loadWishlistSymbols() skipped here; wishlist rarely changes between
    //     refreshes. _syncAllHearts() runs once at end of _loadRemainingStocks.
    await _loadRemainingStocks(true);
  } catch (e) {
    console.error("Background refresh failed:", e);
    // Old data stays on screen — no error overlay needed
  } finally {
    _bgRefreshInProgress = false;
    _hideUpdateIndicator();
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh'; }
  }
}

let totalStocksCount = 0;   // total stocks on the server
let loadedPages      = {};  // track which pages have been fetched

// forceAll = true  → merge mode: re-fetch all pages, update data in-place (background refresh)
// forceAll = false → append mode: fetch only missing pages, add new stocks (initial load)
async function _loadRemainingStocks(forceAll) {
  if (!totalStocksCount) return;
  const totalPages = Math.ceil(totalStocksCount / STOCKS_PER_PAGE);

  for (let pg = 2; pg <= totalPages; pg++) {
    if (!forceAll && loadedPages[pg]) continue;   // skip already-loaded pages on initial load
    try {
      const r = await fetch("/api/stocks?page=" + pg + "&per_page=" + STOCKS_PER_PAGE);
      if (!r.ok) continue;
      const data = await r.json();
      const newStocks = data.stocks || [];

      if (forceAll) {
        // Merge mode: update existing cards in-place, all 80 stay visible
        _mergeStocks(allStocks, newStocks);
      } else {
        // Append mode: add stocks that aren't loaded yet
        const existingSymbols = new Set(allStocks.map(s => s.symbol));
        newStocks.forEach(s => { if (!existingSymbols.has(s.symbol)) allStocks.push(s); });
      }
      loadedPages[pg] = true;
      // H1: No per-page render — defer to single render after all pages complete
    } catch (e) {
      console.error("Background page " + pg + " load failed:", e);
    }
  }

  // Single render pass after all pages are merged — avoids 3 intermediate DOM rebuilds
  backgroundLoadDone = true;
  renderStocks();
  renderSignalStats();
  _saveSignalSnapshot();
  renderGapScanner();
  _syncAllHearts();
}

// ── Background update indicator (subtle pill in refresh bar) ─────────────
function _showUpdateIndicator() {
  var ind = document.getElementById("bg-update-indicator");
  if (!ind) {
    ind = document.createElement("div");
    ind.id = "bg-update-indicator";
    ind.className = "bg-update-indicator";
    ind.innerHTML = '<div class="bg-update-spinner"></div> Updating signals\u2026';
    var bar = document.getElementById("refresh-bar");
    if (bar) bar.appendChild(ind);
  }
  ind.classList.add("show");
}

function _hideUpdateIndicator() {
  var ind = document.getElementById("bg-update-indicator");
  if (ind) ind.classList.remove("show");
}

// ── Merge fresh stock data into existing array (preserves order, no vanishing) ──
// Updates matched symbols in-place; appends genuinely new symbols.
function _mergeStocks(existing, incoming) {
  var incomingMap = {};
  incoming.forEach(function(s) { if (s.symbol) incomingMap[s.symbol] = s; });
  for (var i = 0; i < existing.length; i++) {
    if (incomingMap[existing[i].symbol]) {
      existing[i] = incomingMap[existing[i].symbol];
      delete incomingMap[existing[i].symbol];
    }
  }
  // Append any brand-new symbols (stock list expansion edge-case)
  Object.keys(incomingMap).forEach(function(sym) { existing.push(incomingMap[sym]); });
}

// renderSummaryCards is now handled by renderSignalStats which writes to #summary-cards
function renderSummaryCards() { renderSignalStats(); }

// ── Sort helper ────────────────────────────────────────────────────────────
function _rrValue(s) {
  if (!s.target_price || !s.current_price || !s.stop_loss) return -999;
  const reward = s.target_price - s.current_price;
  const risk   = s.current_price - s.stop_loss;
  return risk > 0 ? reward / risk : -999;
}

function sortStocks(by, btn) {
  activeSort  = by;
  currentPage = 1;
  document.querySelectorAll(".btn-sort").forEach(function(b) { b.classList.remove("active"); });
  if (btn) btn.classList.add("active");
  renderStocks();
}

// Sector-only filter (ignores signal filter) — used for the empty-state hint
function _applySortAndFilterSectorOnly(stocks) {
  if (activeSector === "ALL") return stocks.slice();
  return stocks.filter(function(s) {
    return !s.unavailable && (s.sector || "Others") === activeSector;
  });
}

function _applySortAndFilter(stocks) {
  let filtered = stocks.slice();

  // Signal filter — "BUY" matches both BUY + STRONG BUY; "SELL" matches both SELL + STRONG SELL;
  // exact values like "STRONG BUY" from the pill bar are matched exactly
  if (activeFilter !== "ALL") {
    filtered = filtered.filter(function(s) {
      const sig = s.signal || "HOLD";
      if (activeFilter === "BUY")        return sig.indexOf("BUY")  >= 0;
      if (activeFilter === "SELL")       return sig.indexOf("SELL") >= 0;
      if (activeFilter === "STRONG BUY")  return sig === "STRONG BUY";
      if (activeFilter === "STRONG SELL") return sig === "STRONG SELL";
      return sig === activeFilter;
    });
  }

  // Sector filter
  if (activeSector !== "ALL") {
    filtered = filtered.filter(function(s) {
      return (s.sector || "Others") === activeSector;
    });
  }

  // Sort
  filtered.sort(function(a, b) {
    if (activeSort === "rr")     return _rrValue(b) - _rrValue(a);
    if (activeSort === "change") return Math.abs(b.change_pct||0) - Math.abs(a.change_pct||0);
    if (activeSort === "volume") return (b.volume||0) - (a.volume||0);
    return (b.score||0) - (a.score||0); // default: score
  });

  return filtered;
}

// ── Signal snapshot (for change badge) ────────────────────────────────────
function _saveSignalSnapshot() {
  const snap = {};
  allStocks.forEach(function(s) { if (s.signal && s.symbol) snap[s.symbol] = s.signal; });
  try { localStorage.setItem("_prevSignals", JSON.stringify(snap)); } catch(e) {}
}

function _loadSignalSnapshot() {
  try { prevSignals = JSON.parse(localStorage.getItem("_prevSignals") || "{}"); } catch(e) { prevSignals = {}; }
}

function renderStocks() {
  const grid = document.getElementById("stock-grid");
  if (!grid) return;

  const filtered = _applySortAndFilter(allStocks);

  if (!filtered.length) {
    // Build a helpful empty-state message explaining which filters are blocking
    const sigLabel    = activeFilter !== "ALL" ? activeFilter : null;
    const sectorLabel = activeSector !== "ALL" ? activeSector : null;

    let hint = "";
    if (sigLabel && sectorLabel) {
      // Both filters active — most common cause of empty sectors
      const allInSector = _applySortAndFilterSectorOnly(allStocks);
      hint = '<p class="mb-2">No <strong>' + sigLabel + '</strong> signals in <strong>'
        + sectorLabel + '</strong> sector right now'
        + (allInSector.length ? ' — but there are <strong>' + allInSector.length + ' stocks</strong> with other signals.' : '.')
        + '</p>'
        + '<button class="btn btn-sm btn-outline-primary me-2" onclick="filterStocks(\'ALL\', document.querySelector(\'.btn-filter.all\'))">'
        + 'Show All Signals in ' + sectorLabel + '</button>'
        + '<button class="btn btn-sm btn-outline-secondary" onclick="filterSector(\'ALL\', document.querySelector(\'.btn-filter-sector.active\'))">'
        + 'Show All Sectors</button>';
    } else if (sigLabel) {
      hint = '<p class="mb-2">No stocks with <strong>' + sigLabel + '</strong> signal match the current sector.</p>'
        + '<button class="btn btn-sm btn-outline-primary" onclick="filterStocks(\'ALL\', null)">Show All Signals</button>';
    } else if (sectorLabel) {
      hint = '<p class="mb-2">No stocks in <strong>' + sectorLabel + '</strong> sector loaded yet.</p>';
    } else {
      hint = '<p class="mb-2">No stocks loaded yet.</p>';
    }

    grid.innerHTML = '<div class="col-12 text-center py-5">'
      + '<div style="font-size:2.5rem;margin-bottom:12px;">🔍</div>'
      + hint
      + '</div>';
    renderPagination(0);
    return;
  }

  // Paginate — use server total only when no filter/sort active
  const useServerTotal = (activeFilter === "ALL" && activeSector === "ALL" && activeSort === "score" && totalStocksCount > 0);
  const totalPages = useServerTotal
    ? Math.ceil(totalStocksCount / STOCKS_PER_PAGE)
    : Math.ceil(filtered.length / STOCKS_PER_PAGE);
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;
  const start = (currentPage - 1) * STOCKS_PER_PAGE;
  const pageStocks = filtered.slice(start, start + STOCKS_PER_PAGE);

  grid.innerHTML = pageStocks.map(function(s) { return stockCard(s, false); }).join("");

  // Update stock count to show "X of Y"
  const sc = document.getElementById("stock-count");
  if (sc) sc.textContent = filtered.length;

  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  let container = document.getElementById("pagination-controls");
  if (!container) return;

  if (totalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = '<nav aria-label="Stock pages"><ul class="pagination justify-content-center mb-0">';

  // Previous
  html += '<li class="page-item' + (currentPage === 1 ? ' disabled' : '') + '">'
        + '<a class="page-link" href="#" onclick="goToPage(' + (currentPage - 1) + ');return false;">&laquo; Prev</a></li>';

  // Page numbers — show max 7 pages with ellipsis
  var startPage = Math.max(1, currentPage - 3);
  var endPage = Math.min(totalPages, startPage + 6);
  if (endPage - startPage < 6) startPage = Math.max(1, endPage - 6);

  if (startPage > 1) {
    html += '<li class="page-item"><a class="page-link" href="#" onclick="goToPage(1);return false;">1</a></li>';
    if (startPage > 2) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
  }

  for (var p = startPage; p <= endPage; p++) {
    html += '<li class="page-item' + (p === currentPage ? ' active' : '') + '">'
          + '<a class="page-link" href="#" onclick="goToPage(' + p + ');return false;">' + p + '</a></li>';
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    html += '<li class="page-item"><a class="page-link" href="#" onclick="goToPage(' + totalPages + ');return false;">' + totalPages + '</a></li>';
  }

  // Next
  html += '<li class="page-item' + (currentPage === totalPages ? ' disabled' : '') + '">'
        + '<a class="page-link" href="#" onclick="goToPage(' + (currentPage + 1) + ');return false;">Next &raquo;</a></li>';

  html += '</ul></nav>';

  if (!backgroundLoadDone && allStocks.length > 0) {
    html += '<div class="text-center text-muted small mt-2"><i class="bi bi-hourglass-split me-1"></i>Loading more stocks in background...</div>';
  }

  container.innerHTML = html;
}

async function goToPage(page) {
  currentPage = page;

  // H2: Only fetch on-demand if the page isn't loaded AND no background refresh
  //     is already covering it. During a background refresh all pages are being
  //     re-fetched via _loadRemainingStocks(true) — trust that data instead of
  //     racing with a duplicate fetch that would show a spinner over live cards.
  if (!loadedPages[page] && !_bgRefreshInProgress) {
    const grid = document.getElementById("stock-grid");
    if (grid) grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="text-muted mt-2">Loading page ' + page + '...</div></div>';

    try {
      const r = await fetch("/api/stocks?page=" + page + "&per_page=" + STOCKS_PER_PAGE);
      if (r.ok) {
        const data = await r.json();
        const newStocks = data.stocks || [];
        const existingSymbols = new Set(allStocks.map(s => s.symbol));
        newStocks.forEach(s => { if (!existingSymbols.has(s.symbol)) allStocks.push(s); });
        loadedPages[page] = true;
        renderSummaryCards();
      }
    } catch (e) {
      console.error("Failed to fetch page " + page + ":", e);
    }
  }

  renderStocks();
  _syncAllHearts();
  var grid = document.getElementById("stocks-section");
  if (grid) grid.scrollIntoView({ behavior: "smooth", block: "start" });
}

function stockCard(s, fromWishlist) {
  // ── Unavailable / bad-symbol card ──────────────────────
  if (s.unavailable) {
    const safeSym = (s.symbol || "").replace(/'/g, "\\'");
    return '<div class="col-12 col-sm-6 col-lg-4">'
      + '<div class="stock-card unavailable-card">'
      + '<div class="card-body-inner">'
      + '<div class="d-flex justify-content-between align-items-start mb-2">'
      + '<div><div class="stock-name">' + (s.name || s.symbol) + '</div>'
      + '<div class="stock-symbol">' + s.symbol + '</div></div>'
      + '<span class="signal-badge unavailable">⚠️ NOT FOUND</span>'
      + '</div>'
      + '<p class="text-muted small mt-1 mb-2">' + (s.explanation || "Could not load data for this symbol.") + '</p>'
      + '<button class="btn-remove-wish" onclick="removeFromWishlist(\'' + safeSym + '\',event)">'
      + '<i class="bi bi-x-circle me-1"></i> Remove</button>'
      + '</div></div></div>';
  }

  const sig      = s.signal || "HOLD";
  const sigClass = sig.toLowerCase().replace(/ /g, "-");
  const bandCls  = sig === "STRONG BUY"  ? "strong-buy"
                 : sig === "STRONG SELL" ? "strong-sell"
                 : sig.toLowerCase();
  const chg      = s.change_pct || 0;
  const chgCls   = chg >= 0 ? "up" : "down";
  const chgArrow = chg >= 0 ? "▲" : "▼";
  const scoreBar = '<div class="score-bar-track mt-1">'
    + '<div class="score-bar-fill" style="width:' + (s.score||0) + '%;background:' + (s.signal_color||"#999") + '"></div>'
    + '</div>';
  const isWished = wishlistSymbols.has(s.symbol);
  const heartCls = isWished ? "wishlisted" : "";
  const heartIco = isWished ? "bi-heart-fill" : "bi-heart";
  const safeName = (s.name || s.symbol).replace(/'/g, "\\'");

  const removeBtn = fromWishlist
    ? '<button class="btn-remove-wish" onclick="removeFromWishlist(\'' + s.symbol + '\',event)">'
      + '<i class="bi bi-x-circle me-1"></i> Remove from Wishlist</button>'
    : "";

  // ── Target price chips + R:R ratio ─────────────────────────────
  let targetHtml = "";
  if ((sig === "BUY" || sig === "STRONG BUY") && s.target_price) {
    let rrHtml = "";
    if (s.stop_loss && s.current_price) {
      const reward = s.target_price - s.current_price;
      const risk   = s.current_price - s.stop_loss;
      if (risk > 0) {
        const rr = (reward / risk).toFixed(1);
        const rrCls = parseFloat(rr) >= 2 ? "rr-good" : parseFloat(rr) >= 1 ? "rr-ok" : "rr-poor";
        rrHtml = '<span class="rr-badge ' + rrCls + '">R:R 1:' + rr + '</span>';
      }
    }
    targetHtml = '<div class="target-row">'
      + '<span class="target-chip target-buy-chip">🎯 Target ₹' + fmt(s.target_price) + '</span>'
      + (s.stop_loss ? '<span class="target-chip target-stop-chip">🛑 Stop ₹' + fmt(s.stop_loss) + '</span>' : '')
      + rrHtml
      + '</div>';
  } else if ((sig === "SELL" || sig === "STRONG SELL") && s.target_buy_price) {
    targetHtml = '<div class="target-row">'
      + '<span class="target-chip target-reenter-chip">💡 Re-enter ₹' + fmt(s.target_buy_price) + '</span>'
      + '</div>';
  }

  // ── Signal change badge ─────────────────────────────────────────
  const SIG_RANK = { "STRONG BUY": 5, "BUY": 4, "HOLD": 3, "SELL": 2, "STRONG SELL": 1 };
  let changeBadge = "";
  const prev = prevSignals[s.symbol];
  if (prev && prev !== s.signal) {
    const prevR = SIG_RANK[prev] || 3, currR = SIG_RANK[s.signal] || 3;
    if (currR > prevR)
      changeBadge = '<span class="sig-change-badge upgraded">↑ UPGRADED</span>';
    else
      changeBadge = '<span class="sig-change-badge downgraded">↓ DOWNGRADED</span>';
  }

  // ── Signal timestamp ────────────────────────────────────────────
  const tsHtml = s.analysed_at
    ? '<span class="signal-ts"><i class="bi bi-clock me-1"></i>as of ' + s.analysed_at + '</span>'
    : "";

  // ── Add to Portfolio button ─────────────────────────────────────
  const addPortBtn = '<button class="btn-add-port" onclick="openAddPortModal(\''
    + s.symbol + '\',\'' + safeName + '\',' + (s.current_price || 0) + ',event)">'
    + '<i class="bi bi-plus-circle me-1"></i>Add to Portfolio</button>';

  // RS ratio badge
  var rsBadge = "";
  if (s.rs_ratio != null) {
    var rsClass = s.rs_ratio >= 1.0 ? "rs-badge-up" : "rs-badge-down";
    var rsArrow = s.rs_ratio >= 1.0 ? "▲" : "▼";
    rsBadge = '<span class="rs-badge ' + rsClass + '">' + rsArrow + ' RS ' + s.rs_ratio.toFixed(2) + '</span>';
  }

  // Sector badge
  var sectorBadge = s.sector ? '<span class="sector-badge">' + s.sector + '</span>' : "";

  return '<div class="col-12 col-sm-6 col-lg-4">'
    + '<div class="stock-card signal-' + sigClass + '" onclick="showDetail(\'' + s.symbol + '\')">'
    + '<div class="card-band ' + bandCls + '"></div>'
    + '<button class="btn-heart ' + heartCls + '" id="heart-' + s.symbol + '"'
    + ' onclick="toggleWishlist(\'' + s.symbol + '\',\'' + safeName + '\',event)">'
    + '<i class="bi ' + heartIco + '"></i></button>'
    + '<div class="card-body-inner">'
    + '<div class="d-flex justify-content-between align-items-start mb-2">'
    + '<div><div class="stock-name">' + (s.name||s.symbol) + '</div>'
    + '<div class="stock-symbol">' + s.symbol + ' ' + sectorBadge + '</div></div>'
    + '<span class="signal-badge ' + sig + '">' + (s.signal_emoji||"") + " " + sig + '</span>'
    + changeBadge
    + '</div>'
    + '<div class="stock-price mb-1">₹' + fmt(s.current_price)
    + ' <span class="stock-change ' + chgCls + '">' + chgArrow + " " + Math.abs(chg).toFixed(2) + '%</span></div>'
  + (s.day_high && s.day_low
      ? '<div class="day-hl"><span class="day-h">H ₹' + fmt(s.day_high) + '</span>'
        + '<span class="day-sep">|</span>'
        + '<span class="day-l">L ₹' + fmt(s.day_low) + '</span>'
        + (s.orb_high ? '<span class="orb-tag">ORB</span>' : '')
        + '</div>'
      : '')
    + '<div class="d-flex justify-content-between align-items-center mb-2">'
    + '<small class="text-muted">AI Score: <strong>' + (s.score||0) + '/100</strong></small>'
    + '<div class="d-flex gap-1 align-items-center">'
    + rsBadge
    + '<span class="risk-pill risk-' + (s.risk||"MEDIUM") + '">' + (s.risk||"MEDIUM") + ' RISK</span>'
    + '</div>'
    + '</div>'
    + scoreBar
    + targetHtml
    + tsHtml
    + '<div class="card-footer-row">'
    + addPortBtn
    + removeBtn
    + '</div>'
    + '</div></div></div>';
}

function filterStocks(filter, btn) {
  activeFilter = filter;
  currentPage = 1;
  document.querySelectorAll(".btn-filter").forEach(function(b) { b.classList.remove("active"); });
  if (btn) btn.classList.add("active");
  renderStocks();
}

// Called from the compact signal pill bar (no btn reference needed)
function applyFilter(filter) {
  activeFilter = filter;
  currentPage = 1;
  // Sync .btn-filter buttons if present
  document.querySelectorAll(".btn-filter").forEach(function(b) {
    const bf = b.dataset.filter || b.getAttribute("onclick");
    b.classList.remove("active");
    if (bf && bf.indexOf("'" + filter + "'") >= 0) b.classList.add("active");
  });
  renderStocks();
}

function filterSector(sector, btn) {
  activeSector = sector;
  currentPage = 1;
  document.querySelectorAll(".btn-filter-sector").forEach(function(b) { b.classList.remove("active"); });
  if (btn) btn.classList.add("active");

  // Auto-reset signal filter to ALL when a specific sector is chosen —
  // prevents the confusing "Banking + BUY = 0 results" blank screen
  if (sector !== "ALL" && activeFilter !== "ALL") {
    activeFilter = "ALL";
    document.querySelectorAll(".btn-filter").forEach(function(b) { b.classList.remove("active"); });
    const allBtn = document.querySelector(".btn-filter.all");
    if (allBtn) allBtn.classList.add("active");
  }

  renderStocks();
}

async function showDetail(symbol) {
  currentModalSymbol = symbol;
  const modal = new bootstrap.Modal(document.getElementById("detailModal"));
  modal.show();

  setEl("modal-title", "Loading…");
  setEl("modal-subtitle", "");
  setEl("modal-explanation", "Fetching data…");
  setEl("modal-stats", "");
  setEl("modal-reasons", "");
  setEl("modal-signal-label", "");
  setEl("modal-signal-score", "");

  try {
    const r = await fetch("/api/stock/" + symbol);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const s = await r.json();
    currentModalData = s;  // store for chart TF switching

    // Reset chart TF buttons to 15m
    document.querySelectorAll(".btn-tf").forEach(function(b) { b.classList.remove("active"); });
    const tf15 = document.querySelector(".btn-tf[onclick*=\"'15m'\"]");
    if (tf15) tf15.classList.add("active");

    setEl("modal-title", s.name || symbol);
    setEl("modal-subtitle", symbol + (s.sector ? "  •  " + s.sector : ""));
    setEl("modal-explanation", s.explanation || "");

    const banner = document.getElementById("modal-signal-banner");
    if (banner) {
      banner.className = "signal-banner mb-4 " + s.signal;
      banner.style.background   = s.signal_bg    || "";
      banner.style.borderColor  = s.signal_color || "";
    }
    setEl("modal-signal-label", (s.signal_emoji||"") + " " + s.signal);
    var techWPct = s.tech_weight ? Math.round(s.tech_weight * 100) : 70;
    var sentWPct = s.sent_weight ? Math.round(s.sent_weight * 100) : 30;
    setEl("modal-signal-score",
      "AI Score: " + s.score + "/100  |  "
      + "Technical: " + (s.tech_score ? s.tech_score.toFixed(0) : "?") + " (" + techWPct + "%)  |  "
      + "Sentiment: " + (s.sent_score != null ? s.sent_score.toFixed(0) : "?") + " (" + sentWPct + "%)");

    const hdr = document.getElementById("modal-header");
    if (hdr) hdr.style.background = s.signal_color || "#1a237e";

    const stats = [
      { v: "₹" + fmt(s.current_price),                l: "Current Price"   },
      { v: (s.change_pct||0).toFixed(2) + "%",        l: "Today's Change"  },
      { v: s.day_high ? "₹" + fmt(s.day_high) : "—", l: "📈 Day High"     },
      { v: s.day_low  ? "₹" + fmt(s.day_low)  : "—", l: "📉 Day Low"      },
      { v: fmtVol(s.volume),                           l: "Volume"          },
      { v: fmtVol(s.avg_volume),                       l: "Avg Volume"      },
      { v: "₹" + fmt(s.high_52w),                     l: "52W High"        },
      { v: "₹" + fmt(s.low_52w),                      l: "52W Low"         },
    ];
    // ORB levels (if computed today)
    if (s.orb_high) stats.push({ v: "₹" + fmt(s.orb_high), l: "⚡ ORB High" });
    if (s.orb_low)  stats.push({ v: "₹" + fmt(s.orb_low),  l: "⚡ ORB Low"  });
    // VWAP
    if (s.vwap)  stats.push({ v: "₹" + fmt(s.vwap),  l: "📊 VWAP (today)"  });
    // Support/resistance
    if (s.support_level)    stats.push({ v: "₹" + fmt(s.support_level),    l: "🟩 Support (S1)"   });
    if (s.resistance_level) stats.push({ v: "₹" + fmt(s.resistance_level), l: "🟥 Resistance (R1)"});
    // RS ratio
    if (s.rs_ratio != null) {
      const rsLabel = s.rs_ratio >= 1.0 ? "▲ Outperforming" : "▼ Underperforming";
      stats.push({ v: s.rs_ratio.toFixed(2) + "x  " + rsLabel, l: "📈 RS vs NIFTY 50" });
    }
    // Target price entries (only shown when present)
    if (s.target_price)     stats.push({ v: "₹" + fmt(s.target_price),     l: "🎯 Target Price"    });
    if (s.stop_loss)        stats.push({ v: "₹" + fmt(s.stop_loss),         l: "🛑 Stop Loss"       });
    if (s.target_buy_price) stats.push({ v: "₹" + fmt(s.target_buy_price),  l: "💡 Re-entry Target" });
    // Position sizing
    if (s.suggested_qty)    stats.push({ v: s.suggested_qty + " shares  (₹" + fmt(s.risk_amount) + " at risk)", l: "📐 Suggested Qty" });
    const statsEl = document.getElementById("modal-stats");
    if (statsEl) statsEl.innerHTML = stats.map(function(st) {
      return '<div class="col-6 col-md-4"><div class="stat-box">'
        + '<div class="stat-val">' + (st.v||"—") + '</div>'
        + '<div class="stat-lbl">' + st.l + '</div>'
        + '</div></div>';
    }).join("");

    renderModalChart(s);

    const rEl = document.getElementById("modal-reasons");
    if (rEl) rEl.innerHTML = (s.reasons||[]).map(function(r) { return "<li>" + r + "</li>"; }).join("");

    // ── AI Analysis section ──────────────────────────────────────────────────
    _renderAIAnalysis(s);

    _syncModalWishBtn();
  } catch (e) {
    setEl("modal-title", "Error");
    setEl("modal-explanation", "Could not load stock details. Please try again.");
    console.error(e);
  }
}

function _renderAIAnalysis(s) {
  var section = document.getElementById("ai-analysis-section");
  if (!section) return;

  if (!s.ai_available) {
    section.style.display = "none";
    return;
  }
  section.style.display = "block";

  // Confidence dots
  var confEl = document.getElementById("ai-confidence");
  if (confEl) {
    var conf = (s.ai_confidence || "").toUpperCase();
    var dots = conf === "HIGH" ? "●●●" : conf === "MEDIUM" ? "●●○" : "●○○";
    var confClass = conf === "HIGH" ? "conf-high" : conf === "MEDIUM" ? "conf-med" : "conf-low";
    confEl.className = "ai-confidence-label " + confClass;
    confEl.textContent = dots + " " + conf + " confidence";
  }

  // Agrees / disagrees badge
  var agreeEl = document.getElementById("ai-agrees");
  if (agreeEl) {
    if (s.ai_signal_agrees === true) {
      agreeEl.className = "ai-agrees-label ai-agrees-yes";
      agreeEl.textContent = "✅ AI agrees with " + (s.signal || "signal");
    } else if (s.ai_signal_agrees === false) {
      agreeEl.className = "ai-agrees-label ai-agrees-no";
      agreeEl.textContent = "⚠️ AI disagrees with " + (s.signal || "signal");
    } else {
      agreeEl.textContent = "";
    }
  }

  // Thesis
  setEl("ai-thesis", s.ai_thesis || "");

  // Risk flags
  var flagsWrap = document.getElementById("ai-risk-flags");
  var flagsList = document.getElementById("ai-risk-flags-list");
  if (flagsWrap && flagsList) {
    if (s.ai_risk_flags && s.ai_risk_flags.length > 0) {
      flagsWrap.style.display = "block";
      flagsList.innerHTML = s.ai_risk_flags.map(function(f) { return "<li>" + f + "</li>"; }).join("");
    } else {
      flagsWrap.style.display = "none";
    }
  }

  // Contradictions
  var contrWrap = document.getElementById("ai-contradictions");
  var contrList = document.getElementById("ai-contradictions-list");
  if (contrWrap && contrList) {
    if (s.ai_contradictions && s.ai_contradictions.length > 0) {
      contrWrap.style.display = "block";
      contrList.innerHTML = s.ai_contradictions.map(function(f) { return "<li>" + f + "</li>"; }).join("");
    } else {
      contrWrap.style.display = "none";
    }
  }
}

function switchChartTF(tf, btn) {
  if (!currentModalData) return;
  document.querySelectorAll(".btn-tf").forEach(function(b) { b.classList.remove("active"); });
  if (btn) btn.classList.add("active");
  renderModalChart(currentModalData, tf);
}

function renderModalChart(s, tf) {
  tf = tf || "15m";
  const ctx = document.getElementById("modal-chart");
  if (!ctx) return;
  if (modalChart) { modalChart.destroy(); modalChart = null; }

  let prices = [], labels = [], noteText = "";

  if (tf === "daily" && Array.isArray(s.daily_chart) && s.daily_chart.length) {
    prices    = s.daily_chart.map(function(d) { return d.price; });
    labels    = s.daily_chart.map(function(d) { return d.date;  });
    noteText  = "Showing " + prices.length + " daily candles (1 year)";
  } else if (tf === "1h" && Array.isArray(s.intraday) && s.intraday.length) {
    // Aggregate 15m bars into 1H candles (group every 4 bars)
    var bars = s.intraday;
    for (var i = 0; i < bars.length; i += 4) {
      var group = bars.slice(i, i + 4);
      if (group.length === 0) continue;
      prices.push(group[group.length - 1].price || group[group.length - 1].close);
      // Extract HH:MM from the time string
      var t = group[0].time || "";
      labels.push(t.substring(11, 16) || t.substring(0, 5));
    }
    noteText = "Showing " + prices.length + " hourly bars (1H aggregated)";
  } else {
    // Default: 15m intraday
    if (Array.isArray(s.intraday) && s.intraday.length) {
      prices = s.intraday.map(function(d) { return d.price || d.close; });
      labels = s.intraday.map(function(d) {
        var t = d.time || "";
        return t.substring(11, 16) || t.substring(0, 5) || t;
      });
    } else if (s.intraday && s.intraday.prices) {
      prices = s.intraday.prices;
      labels = s.intraday.labels || [];
    }
    noteText = "Showing " + prices.length + " data points (15-min intervals)";
  }

  const note = document.getElementById("chart-note");

  if (!prices.length) {
    if (note) note.textContent = tf === "daily" ? "No daily chart data available." : "No intraday data available for today.";
    return;
  }

  const color = s.signal_color || "#1a237e";
  modalChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        data: prices,
        borderColor: color,
        backgroundColor: color + "22",
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: tf === "daily" ? 8 : 6, font: { size: 11 } } },
        y: { ticks: { callback: function(v) { return "₹" + v.toLocaleString("en-IN"); } } },
      },
    },
  });
  if (note) note.textContent = noteText;
}

function exportExcel() {
  window.location.href = "/api/export";
}

// ═══════════════════════════════════════════════════════════════ WISHLIST TAB ═

async function loadWishlistSymbols() {
  try {
    const r = await fetch("/api/wishlist");
    if (!r.ok) return;
    const d = await r.json();
    // Lambda returns {"wishlist":[...]}, guard against legacy {"stocks":[...]} too
    const items = d.wishlist || d.stocks || [];
    wishlistSymbols = new Set(items.map(function(s) { return s.symbol; }));
    updateWishlistBadge(items.length);
  } catch (_) {}
}

async function loadWishlistCount() {
  await loadWishlistSymbols();
}

async function loadWishlist() {
  showEl("wishlist-loading");
  hideEl("wishlist-empty");
  const grid = document.getElementById("wishlist-grid");
  if (grid) grid.innerHTML = "";

  try {
    const r = await fetch("/api/wishlist");
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();

    // Lambda returns {"wishlist":[...]}, guard against legacy {"stocks":[...]} too
    const wishItems = d.wishlist || d.stocks || [];
    wishlistSymbols = new Set(wishItems.map(function(s) { return s.symbol; }));
    updateWishlistBadge(wishItems.length);
    setEl("wishlist-count", wishItems.length);

    if (!wishItems.length) {
      hideEl("wishlist-loading");
      showEl("wishlist-empty");
      return;
    }

    // Fetch full analysis for each wishlist stock in parallel
    const analyzed = await Promise.all(
      wishItems.map(async function(item) {
        try {
          const sr = await fetch("/api/stock/" + encodeURIComponent(item.symbol));
          if (!sr.ok) return { symbol: item.symbol, name: item.name, unavailable: true,
                               explanation: "Could not load stock data." };
          const data = await sr.json();
          return (data.error || data.unavailable)
            ? { symbol: item.symbol, name: item.name, unavailable: true,
                explanation: data.error || "No data available." }
            : data;
        } catch (_) {
          return { symbol: item.symbol, name: item.name, unavailable: true,
                   explanation: "Network error fetching data." };
        }
      })
    );

    hideEl("wishlist-loading");
    if (grid) grid.innerHTML = analyzed.map(function(s) { return stockCard(s, true); }).join("");
  } catch (e) {
    hideEl("wishlist-loading");
    showEl("wishlist-empty");
    console.error(e);
  }
}

async function toggleWishlist(symbol, name, event) {
  if (event) { event.stopPropagation(); event.preventDefault(); }
  if (wishlistSymbols.has(symbol)) {
    await removeFromWishlist(symbol, null);
  } else {
    await addToWishlist(symbol, name);
  }
}

async function addToWishlist(symbol, name) {
  try {
    const r = await fetch("/api/wishlist", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ symbol: symbol, name: name }),
    });
    const d = await r.json();
    if (!d.already_exists) {
      wishlistSymbols.add(symbol);
      showToast("❤️ " + name + " added to Wishlist");
    } else {
      showToast(symbol + " is already in your Wishlist");
    }
    updateWishlistBadge(wishlistSymbols.size);
    _syncHeart(symbol);
    _syncModalWishBtn();
  } catch (e) {
    showToast("Could not add to Wishlist. Please try again.");
  }
}

async function removeFromWishlist(symbol, event) {
  if (event) { event.stopPropagation(); event.preventDefault(); }
  try {
    await fetch("/api/wishlist/" + symbol, { method: "DELETE" });
    wishlistSymbols.delete(symbol);
    showToast("💔 " + symbol + " removed from Wishlist");
    updateWishlistBadge(wishlistSymbols.size);
    _syncHeart(symbol);
    _syncModalWishBtn();
    if (currentTab === "wishlist") await loadWishlist();
  } catch (e) {
    showToast("Could not remove from Wishlist. Please try again.");
  }
}

async function addToWishlistManual() {
  const input = document.getElementById("wishlist-input");
  const sym   = (input ? input.value : "").trim().toUpperCase();
  if (!sym) { showToast("Please type a stock symbol first."); return; }
  await addToWishlist(sym, sym);
  if (input) input.value = "";
  // If already on wishlist tab reload in place; otherwise switch (which auto-loads)
  if (currentTab === "wishlist") {
    await loadWishlist();
  } else {
    switchTab("wishlist");
  }
}

function toggleWishlistFromModal() {
  if (!currentModalSymbol) return;
  const name = document.getElementById("modal-title") ? document.getElementById("modal-title").textContent : currentModalSymbol;
  toggleWishlist(currentModalSymbol, name, null);
}

function _syncHeart(symbol) {
  const btn = document.getElementById("heart-" + symbol);
  if (!btn) return;
  const wished = wishlistSymbols.has(symbol);
  btn.classList.toggle("wishlisted", wished);
  const ico = btn.querySelector("i");
  if (ico) ico.className = wished ? "bi bi-heart-fill" : "bi bi-heart";
}

function _syncAllHearts() {
  allStocks.forEach(function(s) { _syncHeart(s.symbol); });
}

function _syncModalWishBtn() {
  if (!currentModalSymbol) return;
  const wished = wishlistSymbols.has(currentModalSymbol);
  const icon   = document.getElementById("modal-wish-icon");
  const label  = document.getElementById("modal-wish-label");
  if (icon)  icon.className    = wished ? "bi bi-heart-fill" : "bi bi-heart";
  if (label) label.textContent = wished ? "Remove from Wishlist" : "Add to Wishlist";
}

function updateWishlistBadge(count) {
  const badge = document.getElementById("wishlist-tab-count");
  if (badge) {
    badge.textContent   = count;
    badge.style.display = count > 0 ? "" : "none";
  }
  const wc = document.getElementById("wishlist-count");
  if (wc) wc.textContent = count;
}

function showToast(msg) {
  const el = document.getElementById("wishlist-toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("d-none");
  clearTimeout(el._timer);
  el._timer = setTimeout(function() { el.classList.add("d-none"); }, 2800);
}

// ═══════════════════════════════════════════════════════════════════ NEWS ════

async function loadNews() {
  const loadingEl = document.getElementById("news-loading");
  const gridEl    = document.getElementById("news-grid");

  try {
    const r = await fetch("/api/news");
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    const news = d.news || [];

    if (loadingEl) loadingEl.style.display = "none";
    if (!gridEl) return;

    if (!news.length) {
      gridEl.innerHTML = '<div class="col-12 text-muted">No news available right now.</div>';
      return;
    }

    gridEl.innerHTML = news.slice(0, 12).map(function(n) {
      return '<div class="col-12 col-md-6 col-lg-4">'
        + '<div class="news-card ' + ((n.sentiment||"neutral").toLowerCase()) + '">'
        + '<a class="news-title" href="' + (n.link||"#") + '" target="_blank" rel="noopener">' + (n.title||"No title") + '</a>'
        + '<div class="news-meta">'
        + (n.source ? '<strong>' + n.source + '</strong> &nbsp;·&nbsp; ' : "")
        + (n.published||"")
        + '<span class="news-sentiment ms-2 ' + (n.sentiment||"Neutral") + '">' + (n.sentiment_icon||"") + " " + (n.sentiment||"Neutral") + '</span>'
        + '</div></div></div>';
    }).join("");
  } catch (e) {
    if (loadingEl) loadingEl.textContent = "Could not load news.";
    console.error(e);
  }
}

// ═══════════════════════════════════════════════════ INDEX STRIP ════

async function loadIndexData() {
  try {
    const r = await fetch("/api/market-status");
    if (!r.ok) return;
    const d = await r.json();

    // Market open/closed badge
    const badge = document.getElementById("market-open-badge");
    if (badge) {
      badge.textContent  = d.is_open ? "OPEN" : "CLOSED";
      badge.className    = "idx-status " + (d.is_open ? "idx-open" : "idx-closed");
    }

    // Adjust refresh interval: 60s during market hours, 300s after hours
    const wasOpen = marketIsOpen;
    marketIsOpen  = d.is_open || false;
    if (marketIsOpen !== wasOpen) {
      // Market open/close state changed — restart countdown with new interval
      startCountdown();
    }
    // Update refresh label to reflect current interval
    const refreshLabel = document.getElementById("refresh-interval-label");
    if (refreshLabel) {
      refreshLabel.textContent = marketIsOpen ? "60s" : "5m";
    }

    const indices = d.indices || {};

    function _setIdx(priceId, chgId, label) {
      const info = indices[label] || {};
      const price = info.price;
      const chg   = info.change_pct;

      const priceEl = document.getElementById(priceId);
      const chgEl   = document.getElementById(chgId);

      if (priceEl) priceEl.textContent = price != null
        ? Number(price).toLocaleString("en-IN", { maximumFractionDigits: 2 })
        : "—";

      if (chgEl) {
        if (chg != null) {
          const sign  = chg >= 0 ? "+" : "";
          chgEl.textContent = sign + chg.toFixed(2) + "%";
          chgEl.className   = "idx-chg " + (chg >= 0 ? "idx-up" : "idx-down");
        } else {
          chgEl.textContent = "—";
        }
      }
    }

    _setIdx("idx-nifty-price", "idx-nifty-chg",  "NIFTY 50");
    _setIdx("idx-bank-price",  "idx-bank-chg",   "BANKNIFTY");
    _setIdx("idx-vix-price",   "idx-vix-chg",    "India VIX");

  } catch (_) {}
}

// ══════════════════════════════════════════════════ GAP SCANNER ════

function renderGapScanner() {
  const strip = document.getElementById("gap-strip-inner");
  if (!strip || !allStocks.length) return;

  // Sort by absolute change_pct, take top 10
  const sorted = allStocks
    .filter(function(s) { return s.change_pct != null && !s.unavailable; })
    .sort(function(a, b) { return Math.abs(b.change_pct) - Math.abs(a.change_pct); })
    .slice(0, 10);

  strip.innerHTML = sorted.map(function(s) {
    const chg   = s.change_pct || 0;
    const isUp  = chg >= 0;
    const cls   = isUp ? "gp-up" : "gp-down";
    const arrow = isUp ? "▲" : "▼";
    return '<span class="gap-pill ' + cls + '" onclick="showDetail(\'' + s.symbol + '\')" title="' + (s.name||s.symbol) + '">'
      + '<span class="gp-sym">' + s.symbol.replace(".NS","") + '</span>'
      + '<span class="gp-chg">' + arrow + ' ' + Math.abs(chg).toFixed(2) + '%</span>'
      + '<span class="gp-price">₹' + fmt(s.current_price) + '</span>'
      + '</span>';
  }).join("");

  showEl("gap-strip");
}

// ═══════════════════════════════════════════ SIGNAL STATS (Feature 10) ════
// Renders into summary-cards — replaces the 4 basic count cards with a richer view.

function renderSignalStats() {
  const el = document.getElementById("summary-cards");
  if (!el || !allStocks.length) return;

  const valid = allStocks.filter(function(s) { return !s.unavailable && s.signal; });
  if (!valid.length) return;

  const counts = { "STRONG BUY": 0, "BUY": 0, "HOLD": 0, "SELL": 0, "STRONG SELL": 0 };
  const scores = { "STRONG BUY": [], "BUY": [], "HOLD": [], "SELL": [], "STRONG SELL": [] };
  let totalScore = 0;

  valid.forEach(function(s) {
    if (counts[s.signal] !== undefined) {
      counts[s.signal]++;
      scores[s.signal].push(s.score || 0);
    }
    totalScore += s.score || 0;
  });

  const avgAll = valid.length ? Math.round(totalScore / valid.length) : 0;

  const top5Buy = valid
    .filter(function(s) { return s.signal === "STRONG BUY" || s.signal === "BUY"; })
    .sort(function(a,b) { return (b.score||0) - (a.score||0); })
    .slice(0, 5);

  const defs = [
    { sig: "STRONG BUY",  emoji: "🟢", cls: "sp-sbuy"  },
    { sig: "BUY",         emoji: "✅", cls: "sp-buy"   },
    { sig: "HOLD",        emoji: "🟡", cls: "sp-hold"  },
    { sig: "SELL",        emoji: "🔴", cls: "sp-sell"  },
    { sig: "STRONG SELL", emoji: "⛔", cls: "sp-ssell" },
  ];

  // Compact pill bar (single row)
  const pillsHtml = defs.map(function(d) {
    const cnt = counts[d.sig];
    const label = d.sig === "STRONG BUY" ? "S.BUY" : d.sig === "STRONG SELL" ? "S.SELL" : d.sig;
    return '<div class="sig-pill ' + d.cls + (cnt === 0 ? " sp-zero" : "") + '" '
      + 'onclick="applyFilter(\'' + d.sig + '\')" title="Filter: ' + d.sig + '">'
      + '<span class="sp-emoji">' + d.emoji + '</span>'
      + '<span class="sp-label">' + label + '</span>'
      + '<span class="sp-count">' + cnt + '</span>'
      + '</div>';
  }).join("");

  // Avg score badge
  const avgBadge = '<div class="sig-pill sp-avg" title="Average AI score across all stocks">'
    + '<span class="sp-emoji">🤖</span>'
    + '<span class="sp-label">AVG</span>'
    + '<span class="sp-count">' + avgAll + '</span>'
    + '</div>';

  // Top picks row
  const topsHtml = top5Buy.length
    ? '<div class="sig-top-picks">'
        + '<span class="stp-label">🏆 Top picks:</span>'
        + top5Buy.map(function(s) {
            return '<span class="top-pick-chip" onclick="showDetail(\'' + s.symbol + '\')">'
              + s.symbol.replace(".NS","") + ' <strong>' + (s.score||0) + '</strong></span>';
          }).join("")
      + '</div>'
    : "";

  el.innerHTML = '<div class="col-12">'
    + '<div class="sig-pill-bar">'
    + pillsHtml
    + '<div class="sp-divider"></div>'
    + avgBadge
    + '<span class="sp-total">' + valid.length + ' stocks</span>'
    + '</div>'
    + topsHtml
    + '</div>';
}

// ═══════════════════════════════════════════════════════════════ COUNTDOWN ════

function startCountdown() {
  // 60s during market hours (9:15–3:30 IST), 300s after hours
  const interval = () => marketIsOpen ? 60 : 300;
  countdownSecs = interval();

  const txt = document.getElementById("countdown");
  const bar = document.getElementById("refresh-progress");

  if (countdownTimer) clearInterval(countdownTimer);

  countdownTimer = setInterval(function() {
    // While a refresh is in-flight, hold at 0 — don't decrement or re-trigger
    if (_bgRefreshInProgress) {
      if (txt) txt.textContent = "\u27F3";
      if (bar) bar.style.width = "100%";
      return;
    }

    countdownSecs--;
    const total = interval();
    if (txt) txt.textContent = countdownSecs;
    if (bar) bar.style.width = ((total - countdownSecs) / total * 100) + "%";

    if (countdownSecs <= 0) {
      // Pause countdown at 0 until refresh completes — gives user a full
      // 60s of usable data between refreshes (not 60s minus load time)
      countdownSecs = 0;
      if (txt) txt.textContent = "\u27F3";  // ⟳ cycle symbol = "refreshing now"

      if (document.visibilityState === "visible") {
        // loadStocks returns a promise; restart countdown AFTER it finishes
        loadStocks(true).then(function() {
          countdownSecs = interval();
        }).catch(function() {
          countdownSecs = interval();
        });
        loadNews();
      } else {
        countdownSecs = interval();
      }
      loadIndexData(); // always ping market status (cheap — 256MB, ~1s)
    }
  }, 1000);
}

// ═══════════════════════════════════════════════════════════════ HELPERS ════

function showEl(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("d-none");
}
function hideEl(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("d-none");
}
function setEl(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

function fmt(val) {
  if (val == null || isNaN(val)) return "—";
  return Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtVol(val) {
  if (val == null || isNaN(val)) return "—";
  const n = Number(val);
  if (n >= 1e7) return (n / 1e7).toFixed(1) + " Cr";
  if (n >= 1e5) return (n / 1e5).toFixed(1) + " L";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + " K";
  return n.toLocaleString("en-IN");
}

// ═══════════════════════════════════════════════════════════════ AI CHAT ════

let chatSessionId = null;   // Bedrock session ID — persists for multi-turn conversation
let chatBusy      = false;  // prevent double-send while AI is responding

/** Generate a random session ID (UUID v4-style). */
function _newSessionId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

/** Handle Enter key in chat textarea (Enter = send, Shift+Enter = newline). */
function handleChatKey(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChatMessage();
  }
}

/** Send a suggested question by pre-filling the input and sending. */
function sendSuggestion(text) {
  const input = document.getElementById("chat-input");
  if (input) input.value = text;
  sendChatMessage();
}

/** Main send function — reads input, appends user bubble, calls /api/chat. */
async function sendChatMessage() {
  if (chatBusy) return;

  const input = document.getElementById("chat-input");
  const msg   = input ? input.value.trim() : "";
  if (!msg) return;

  // Ensure session ID
  if (!chatSessionId) {
    chatSessionId = sessionStorage.getItem("chat_session_id");
    if (!chatSessionId) {
      chatSessionId = _newSessionId();
      sessionStorage.setItem("chat_session_id", chatSessionId);
    }
  }

  // Clear input, lock UI
  input.value   = "";
  chatBusy      = true;
  const sendBtn = document.getElementById("chat-send-btn");
  if (sendBtn) sendBtn.disabled = true;

  // Hide suggestions after first message
  const sugg = document.getElementById("chat-suggestions");
  if (sugg) sugg.style.display = "none";

  // Render user bubble
  _appendChatBubble("user", msg);

  // Show typing indicator
  const typing = document.getElementById("chat-typing");
  if (typing) typing.classList.remove("d-none");

  // Scroll to bottom
  _scrollChatToBottom();

  try {
    const resp = await fetch("/api/chat", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ message: msg, session_id: chatSessionId }),
    });

    const data = await resp.json();

    if (typing) typing.classList.add("d-none");

    if (resp.ok && data.response) {
      // Update session ID if Bedrock returned a new one
      if (data.session_id) {
        chatSessionId = data.session_id;
        sessionStorage.setItem("chat_session_id", chatSessionId);
      }
      _appendChatBubble("ai", data.response);
    } else {
      const errMsg = data.error || `Error ${resp.status}: could not get a response.`;
      _appendChatBubble("error", errMsg);
    }
  } catch (err) {
    if (typing) typing.classList.add("d-none");
    _appendChatBubble("error", "Network error — please check your connection and try again.");
  }

  chatBusy = false;
  if (sendBtn) sendBtn.disabled = false;
  if (input)  input.focus();
  _scrollChatToBottom();
}

/**
 * Append a chat bubble to the chat window.
 * @param {"user"|"ai"|"error"} role
 * @param {string} text
 */
function _appendChatBubble(role, text) {
  const win = document.getElementById("chat-window");
  if (!win) return;

  // Remove welcome message on first real message
  const welcome = win.querySelector(".chat-welcome");
  if (welcome) welcome.remove();

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble chat-bubble-" + role;

  if (role === "ai") {
    // Convert markdown-style **bold** and line breaks
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");
    bubble.innerHTML = `<div class="bubble-icon">🤖</div><div class="bubble-text">${formatted}</div>`;
  } else if (role === "user") {
    bubble.innerHTML = `<div class="bubble-text">${_escHtml(text)}</div><div class="bubble-icon">👤</div>`;
  } else {
    // error
    bubble.innerHTML = `<div class="bubble-icon">⚠️</div><div class="bubble-text text-danger">${_escHtml(text)}</div>`;
  }

  win.appendChild(bubble);
}

function _scrollChatToBottom() {
  const win = document.getElementById("chat-window");
  if (win) win.scrollTop = win.scrollHeight;
}

function _escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/\n/g, "<br>");
}

// ════════════════════════════════════════════════════ MY PORTFOLIO ════

/** Open "Add to Portfolio" modal, pre-filled with stock details. */
function openAddPortModal(symbol, name, price, event) {
  if (event) { event.stopPropagation(); event.preventDefault(); }
  document.getElementById("port-symbol").value    = symbol;
  document.getElementById("port-buy-price").value  = price || "";
  document.getElementById("port-qty").value         = 1;
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("port-buy-date").value   = today;

  var nameEl   = document.getElementById("port-name");
  var searchEl = document.getElementById("port-search-wrap");
  var searchIn = document.getElementById("port-search-input");

  if (symbol) {
    // Called from a stock card — show static name, hide search
    nameEl.textContent = name + " (" + symbol + ")";
    nameEl.classList.remove("d-none");
    if (searchEl) searchEl.classList.add("d-none");
  } else {
    // Called from "Add Stock" button — show search input
    nameEl.classList.add("d-none");
    nameEl.textContent = "";
    if (searchEl) searchEl.classList.remove("d-none");
    if (searchIn) searchIn.value = "";
  }

  new bootstrap.Modal(document.getElementById("addPortModal")).show();
  // Focus the search input if visible
  if (!symbol && searchIn) setTimeout(function() { searchIn.focus(); }, 300);
}

function onPortSearchInput() {
  var input = document.getElementById("port-search-input");
  var sugg  = document.getElementById("port-search-suggestions");
  if (!input || !sugg) return;
  var q = input.value.trim().toUpperCase();
  if (q.length < 1) { sugg.classList.add("d-none"); return; }

  var matches = knownStocks.filter(function(s) {
    return s.symbol.toUpperCase().indexOf(q) >= 0 || s.name.toUpperCase().indexOf(q) >= 0;
  }).slice(0, 8);

  if (!matches.length) { sugg.classList.add("d-none"); return; }

  sugg.innerHTML = matches.map(function(s) {
    return '<div class="suggestion-item" onclick="selectPortStock(\'' + s.symbol.replace(/'/g, "\\'") + '\',\'' + s.name.replace(/'/g, "\\'") + '\')">'
         + '<strong>' + s.symbol + '</strong> <span class="text-muted">— ' + s.name + '</span></div>';
  }).join("");
  sugg.classList.remove("d-none");
}

function selectPortStock(symbol, name) {
  document.getElementById("port-symbol").value = symbol;
  document.getElementById("port-search-input").value = name + " (" + symbol + ")";
  document.getElementById("port-search-suggestions").classList.add("d-none");
}

/** POST a new holding to /api/portfolio. */
async function addHolding() {
  const symbol   = (document.getElementById("port-symbol").value   || "").trim();
  const name     = (document.getElementById("port-name").textContent || symbol).replace(/\s*\(.*\)/, "").trim();
  const buyPrice = parseFloat(document.getElementById("port-buy-price").value);
  const qty      = parseInt(document.getElementById("port-qty").value, 10);
  const buyDate  = document.getElementById("port-buy-date").value;

  if (!symbol || isNaN(buyPrice) || buyPrice <= 0 || isNaN(qty) || qty <= 0) {
    showToast("Please fill in all fields correctly."); return;
  }
  try {
    const r = await fetch("/api/portfolio", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ symbol, name, buy_price: buyPrice, quantity: qty, buy_date: buyDate }),
    });
    const d = await r.json();
    if (!r.ok) { showToast("Could not add holding: " + (d.error || r.status)); return; }
    bootstrap.Modal.getInstance(document.getElementById("addPortModal")).hide();
    showToast("✅ " + symbol + " added to portfolio!");
    if (currentTab === "portfolio") loadPortfolio();
  } catch (e) {
    showToast("Network error. Please try again.");
  }
}

/** DELETE a holding from /api/portfolio/{holding_id}. */
async function removeHolding(holdingId, symbol, event) {
  if (event) { event.stopPropagation(); event.preventDefault(); }
  if (!confirm("Remove " + symbol + " from your portfolio?")) return;
  try {
    await fetch("/api/portfolio/" + encodeURIComponent(holdingId), { method: "DELETE" });
    showToast("🗑️ " + symbol + " removed from portfolio.");
    loadPortfolio();
  } catch (e) {
    showToast("Could not remove holding. Please try again.");
  }
}

/** Load portfolio holdings and render the dashboard. */
async function loadPortfolio() {
  showEl("portfolio-loading");
  hideEl("portfolio-empty");
  const summary = document.getElementById("portfolio-summary");
  const table   = document.getElementById("portfolio-table-body");
  if (summary) summary.innerHTML = "";
  if (table)   table.innerHTML   = "";

  try {
    const r = await fetch("/api/portfolio");
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    hideEl("portfolio-loading");

    const holdings = d.holdings || [];
    if (!holdings.length) { showEl("portfolio-empty"); return; }

    renderPortfolioSummary(d.summary || {});
    renderPortfolioTable(holdings);
  } catch (e) {
    hideEl("portfolio-loading");
    showEl("portfolio-empty");
    console.error(e);
  }
}

function renderPortfolioSummary(s) {
  const el = document.getElementById("portfolio-summary");
  if (!el) return;
  const gain     = s.total_gain    || 0;
  const dayGain  = s.day_gain      || 0;
  const gainCls  = gain    >= 0 ? "port-pos" : "port-neg";
  const dayCls   = dayGain >= 0 ? "port-pos" : "port-neg";
  const gainArrow  = gain    >= 0 ? "▲" : "▼";
  const dayArrow   = dayGain >= 0 ? "▲" : "▼";

  el.innerHTML =
    portSummaryCard("💰", "Invested",      "₹" + fmt(s.total_invested),  "")
  + portSummaryCard("📈", "Current Value", "₹" + fmt(s.current_value),   "")
  + portSummaryCard("📊", "Total P&L",
      '<span class="' + gainCls + '">' + gainArrow + ' ₹' + fmt(Math.abs(gain)) + '</span>',
      '<span class="' + gainCls + '">' + (s.total_gain_pct||0).toFixed(2) + '%</span>')
  + portSummaryCard("📅", "Today's P&L",
      '<span class="' + dayCls + '">' + dayArrow + ' ₹' + fmt(Math.abs(dayGain)) + '</span>',
      "");
}

function portSummaryCard(icon, label, value, sub) {
  return '<div class="col-6 col-md-3">'
    + '<div class="port-summary-card">'
    + '<div class="port-summary-icon">' + icon + '</div>'
    + '<div class="port-summary-val">'  + value + '</div>'
    + (sub ? '<div class="port-summary-sub">' + sub + '</div>' : '')
    + '<div class="port-summary-lbl">'  + label + '</div>'
    + '</div></div>';
}

function renderPortfolioTable(holdings) {
  const tbody = document.getElementById("portfolio-table-body");
  if (!tbody) return;
  tbody.innerHTML = holdings.map(function(h) {
    const tGain    = h.total_gain    || 0;
    const dGain    = h.day_gain      || 0;
    const tCls     = tGain >= 0 ? "port-pos" : "port-neg";
    const dCls     = dGain >= 0 ? "port-pos" : "port-neg";
    const tArrow   = tGain >= 0 ? "▲" : "▼";
    const dArrow   = dGain >= 0 ? "▲" : "▼";
    const safeSym  = (h.symbol || "").replace(/'/g, "\\'");
    const safeId   = (h.holding_id || "").replace(/'/g, "\\'");

    return '<tr>'
      + '<td><div class="fw-bold">' + (h.name||h.symbol) + '</div>'
      + '<div class="text-muted small">' + h.symbol + '</div></td>'
      + '<td>₹' + fmt(h.buy_price) + '</td>'
      + '<td>' + (h.current_price ? '₹' + fmt(h.current_price) : '<span class="text-muted">—</span>') + '</td>'
      + '<td>' + (h.quantity||0) + '</td>'
      + '<td>₹' + fmt(h.invested) + '</td>'
      + '<td>' + (h.current_value ? '₹' + fmt(h.current_value) : '—') + '</td>'
      + '<td class="' + dCls + '">' + dArrow + ' ₹' + fmt(Math.abs(dGain))
      + '<div class="small">' + (h.day_gain_pct||0).toFixed(2) + '%</div></td>'
      + '<td class="' + tCls + '">' + tArrow + ' ₹' + fmt(Math.abs(tGain))
      + '<div class="small">' + (h.total_gain_pct||0).toFixed(2) + '%</div></td>'
      + '<td><button class="btn-remove-hold" onclick="removeHolding(\'' + safeId + '\',\'' + safeSym + '\',event)">'
      + '<i class="bi bi-x-circle"></i></button></td>'
      + '</tr>';
  }).join("");
}


// (showEl / hideEl already defined above — used throughout)
