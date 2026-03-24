/* ======================================================
   AI Trading Assistant  –  app.js
   Tabs: Intraday | Wishlist | AI Chat
   ====================================================== */

"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
let allStocks          = [];
let activeFilter       = "ALL";
let modalChart         = null;
let wishlistSymbols    = new Set();
let currentModalSymbol = null;
let currentTab         = "intraday";
let countdownTimer     = null;
let countdownSecs      = 900;
let knownStocks        = [];
let currentPage        = 1;
const STOCKS_PER_PAGE  = 10;
let backgroundLoadDone = false;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadMarketStatus();
  loadStocks(false);
  loadNews();
  loadWishlistCount();
  loadKnownStocks();
  startCountdown();
  setInterval(loadMarketStatus, 60_000);

  // Close autocomplete dropdown when clicking outside the input wrapper
  document.addEventListener("click", function(e) {
    const wrap = document.querySelector(".wishlist-input-wrap");
    const sugg = document.getElementById("search-suggestions");
    if (sugg && wrap && !wrap.contains(e.target)) {
      sugg.classList.add("d-none");
    }
  });
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
  if (tab === "wishlist")   loadWishlist();
  if (tab === "portfolio")  loadPortfolio();
}

function refreshCurrentTab() {
  if (currentTab === "intraday")   loadStocks(true);
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
async function loadMarketStatus() {
  try {
    const r = await fetch("/api/market-status");
    if (!r.ok) return;
    const d = await r.json();

    const badgeIn = document.getElementById("badge-in");
    if (d.indian) {
      badgeIn.textContent = "🇮🇳 India — " + d.indian.time + " " + d.indian.label;
      badgeIn.className   = "badge-market " + (d.indian.open ? "open" : "closed");
    }
  } catch (_) {}
}

// ═══════════════════════════════════════════════════════════════ INTRADAY TAB ═

async function loadStocks(forceRefresh) {
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
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading…'; }

  try {
    // Phase 1: Fetch first page quickly
    const r = await fetch("/api/stocks?page=1&per_page=" + STOCKS_PER_PAGE);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const data = await r.json();

    allStocks = data.stocks || [];

    const lu = document.getElementById("last-updated-text");
    if (lu) lu.textContent = "Updated: " + (data.last_updated || "");

    renderSummaryCards();
    renderStocks();

    hideEl("loading-section");
    showEl("summary-row");
    showEl("stocks-section");

    // Sync wishlist hearts
    await loadWishlistSymbols();
    _syncAllHearts();

    // Phase 2: Fetch all remaining stocks in background
    _loadRemainingStocks();
  } catch (e) {
    console.error(e);
    hideEl("loading-section");
    showEl("error-section");
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh'; }
  }
}

async function _loadRemainingStocks() {
  try {
    const r = await fetch("/api/stocks");
    if (!r.ok) return;
    const data = await r.json();

    allStocks = data.stocks || [];
    backgroundLoadDone = true;

    const lu = document.getElementById("last-updated-text");
    if (lu && data.last_updated) lu.textContent = "Updated: " + data.last_updated;

    renderSummaryCards();
    renderStocks();
    _syncAllHearts();
  } catch (e) {
    console.error("Background stock load failed:", e);
    backgroundLoadDone = true;
    renderStocks(); // re-render to remove "loading more" message
  }
}

function renderSummaryCards() {
  const counts = { BUY: 0, HOLD: 0, SELL: 0 };
  let totalScore = 0;
  allStocks.forEach(function(s) {
    const sig = (s.signal || "HOLD").indexOf("BUY")  >= 0 ? "BUY"
              : (s.signal || "HOLD").indexOf("SELL") >= 0 ? "SELL" : "HOLD";
    counts[sig]++;
    totalScore += s.score || 50;
  });
  const avg = allStocks.length ? Math.round(totalScore / allStocks.length) : 0;

  const html = '<div class="col-6 col-md-3">'
    + '<div class="summary-card sbuy">'
    + '<div class="s-count text-success">' + counts.BUY + '</div>'
    + '<div class="s-label">🟢 Buy Signals</div></div></div>'
    + '<div class="col-6 col-md-3">'
    + '<div class="summary-card shold">'
    + '<div class="s-count text-warning">' + counts.HOLD + '</div>'
    + '<div class="s-label">🟡 Hold Signals</div></div></div>'
    + '<div class="col-6 col-md-3">'
    + '<div class="summary-card ssell">'
    + '<div class="s-count text-danger">' + counts.SELL + '</div>'
    + '<div class="s-label">🔴 Sell Signals</div></div></div>'
    + '<div class="col-6 col-md-3">'
    + '<div class="summary-card sother">'
    + '<div class="s-count">' + avg + '</div>'
    + '<div class="s-label">📊 Avg. AI Score</div></div></div>';

  const el = document.getElementById("summary-cards");
  if (el) el.innerHTML = html;
}

function renderStocks() {
  const grid = document.getElementById("stock-grid");
  if (!grid) return;

  const filtered = activeFilter === "ALL" ? allStocks
    : allStocks.filter(function(s) {
        const sig = s.signal || "HOLD";
        if (activeFilter === "BUY")  return sig.indexOf("BUY")  >= 0;
        if (activeFilter === "SELL") return sig.indexOf("SELL") >= 0;
        return sig === "HOLD";
      });

  if (!filtered.length) {
    grid.innerHTML = '<div class="col-12 text-center text-muted py-4">No stocks match this filter.</div>';
    renderPagination(0);
    return;
  }

  // Paginate
  const totalPages = Math.ceil(filtered.length / STOCKS_PER_PAGE);
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

function goToPage(page) {
  currentPage = page;
  renderStocks();
  // Scroll to top of stock grid
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

  // ── Target price chips ──────────────────────────────────────────
  let targetHtml = "";
  if ((sig === "BUY" || sig === "STRONG BUY") && s.target_price) {
    targetHtml = '<div class="target-row">'
      + '<span class="target-chip target-buy-chip">🎯 Target ₹' + fmt(s.target_price) + '</span>'
      + (s.stop_loss ? '<span class="target-chip target-stop-chip">🛑 Stop ₹' + fmt(s.stop_loss) + '</span>' : '')
      + '</div>';
  } else if ((sig === "SELL" || sig === "STRONG SELL") && s.target_buy_price) {
    targetHtml = '<div class="target-row">'
      + '<span class="target-chip target-reenter-chip">💡 Re-enter ₹' + fmt(s.target_buy_price) + '</span>'
      + '</div>';
  }

  // ── Add to Portfolio button ─────────────────────────────────────
  const addPortBtn = '<button class="btn-add-port" onclick="openAddPortModal(\''
    + s.symbol + '\',\'' + safeName + '\',' + (s.current_price || 0) + ',event)">'
    + '<i class="bi bi-plus-circle me-1"></i>Add to Portfolio</button>';

  return '<div class="col-12 col-sm-6 col-lg-4">'
    + '<div class="stock-card signal-' + sigClass + '" onclick="showDetail(\'' + s.symbol + '\')">'
    + '<div class="card-band ' + bandCls + '"></div>'
    + '<button class="btn-heart ' + heartCls + '" id="heart-' + s.symbol + '"'
    + ' onclick="toggleWishlist(\'' + s.symbol + '\',\'' + safeName + '\',event)">'
    + '<i class="bi ' + heartIco + '"></i></button>'
    + '<div class="card-body-inner">'
    + '<div class="d-flex justify-content-between align-items-start mb-2">'
    + '<div><div class="stock-name">' + (s.name||s.symbol) + '</div>'
    + '<div class="stock-symbol">' + s.symbol + '</div></div>'
    + '<span class="signal-badge ' + sig + '">' + (s.signal_emoji||"") + " " + sig + '</span>'
    + '</div>'
    + '<div class="stock-price mb-1">₹' + fmt(s.current_price)
    + ' <span class="stock-change ' + chgCls + '">' + chgArrow + " " + Math.abs(chg).toFixed(2) + '%</span></div>'
    + '<div class="d-flex justify-content-between align-items-center mb-2">'
    + '<small class="text-muted">AI Score: <strong>' + (s.score||0) + '/100</strong></small>'
    + '<span class="risk-pill risk-' + (s.risk||"MEDIUM") + '">' + (s.risk||"MEDIUM") + ' RISK</span>'
    + '</div>'
    + scoreBar
    + targetHtml
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

    setEl("modal-title", s.name || symbol);
    setEl("modal-subtitle", symbol);
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
      { v: "₹" + fmt(s.high_52w),                     l: "52W High"        },
      { v: "₹" + fmt(s.low_52w),                      l: "52W Low"         },
      { v: fmtVol(s.volume),                           l: "Volume"          },
      { v: fmtVol(s.avg_volume),                       l: "Avg Volume"      },
    ];
    // Target price entries (only shown when present)
    if (s.target_price)     stats.push({ v: "₹" + fmt(s.target_price),     l: "🎯 Target Price"    });
    if (s.stop_loss)        stats.push({ v: "₹" + fmt(s.stop_loss),         l: "🛑 Stop Loss"       });
    if (s.target_buy_price) stats.push({ v: "₹" + fmt(s.target_buy_price),  l: "💡 Re-entry Target" });
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

    _syncModalWishBtn();
  } catch (e) {
    setEl("modal-title", "Error");
    setEl("modal-explanation", "Could not load stock details. Please try again.");
    console.error(e);
  }
}

function renderModalChart(s) {
  const ctx = document.getElementById("modal-chart");
  if (!ctx) return;
  if (modalChart) { modalChart.destroy(); modalChart = null; }

  // Backend returns intraday as [{time, price}, ...] array
  let prices = [], labels = [];
  if (Array.isArray(s.intraday) && s.intraday.length) {
    prices = s.intraday.map(function(d) { return d.price; });
    labels = s.intraday.map(function(d) { return d.time;  });
  } else if (s.intraday && s.intraday.prices) {
    prices = s.intraday.prices;
    labels = s.intraday.labels || [];
  }
  const note   = document.getElementById("chart-note");

  if (!prices.length) {
    if (note) note.textContent = "No intraday data available for today.";
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
        x: { ticks: { maxTicksLimit: 6, font: { size: 11 } } },
        y: { ticks: { callback: function(v) { return "₹" + v.toLocaleString("en-IN"); } } },
      },
    },
  });
  if (note) note.textContent = "Showing " + prices.length + " data points (15-min intervals)";
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

// ═══════════════════════════════════════════════════════════════ COUNTDOWN ════

function startCountdown() {
  countdownSecs = 900;
  const txt = document.getElementById("countdown");
  const bar = document.getElementById("refresh-progress");

  if (countdownTimer) clearInterval(countdownTimer);

  countdownTimer = setInterval(function() {
    countdownSecs--;
    if (txt) txt.textContent = countdownSecs;
    if (bar) bar.style.width = ((900 - countdownSecs) / 900 * 100) + "%";

    if (countdownSecs <= 0) {
      countdownSecs = 900;
      loadStocks(true);
      loadNews();
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
