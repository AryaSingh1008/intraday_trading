/* ======================================================
   AI Trading Assistant  –  app.js
   3-tab layout: Intraday | Options | Wishlist
   ====================================================== */

"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
let allStocks          = [];
let activeFilter       = "ALL";
let modalChart         = null;
let wishlistSymbols    = new Set();
let currentModalSymbol = null;
let currentTab         = "intraday";
let currentOptionsSym  = "NIFTY";
let countdownTimer     = null;
let countdownSecs      = 300;
let knownStocks        = [];

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
  if (tab === "options") {
    loadOptions(currentOptionsSym);
  } else if (tab === "wishlist") {
    loadWishlist();
  }
}

function refreshCurrentTab() {
  if (currentTab === "intraday") {
    loadStocks(true);
  } else if (currentTab === "options") {
    loadOptions(currentOptionsSym, true);
  } else if (currentTab === "wishlist") {
    loadWishlist();
  }
}

// ── Autocomplete ──────────────────────────────────────────────────────────────

async function loadKnownStocks() {
  try {
    const r = await fetch("/api/stocks/list");
    if (!r.ok) return;
    const d = await r.json();
    knownStocks = d.stocks || [];
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
    return s.symbol.toUpperCase().indexOf(qU) === 0
        || s.name.toUpperCase().indexOf(qU) >= 0;
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

  const btn = document.getElementById("refresh-btn");
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading…'; }

  try {
    const r = await fetch("/api/stocks");
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

    const sc = document.getElementById("stock-count");
    if (sc) sc.textContent = allStocks.length;

    // Sync wishlist hearts
    await loadWishlistSymbols();
    _syncAllHearts();
  } catch (e) {
    console.error(e);
    hideEl("loading-section");
    showEl("error-section");
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh'; }
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
    return;
  }

  grid.innerHTML = filtered.map(function(s) { return stockCard(s, false); }).join("");
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
    + removeBtn
    + '<div class="card-click-hint mt-2">Tap card for full analysis</div>'
    + '</div></div></div>';
}

function filterStocks(filter, btn) {
  activeFilter = filter;
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

  const prices = s.intraday && s.intraday.prices ? s.intraday.prices : [];
  const labels = s.intraday && s.intraday.labels ? s.intraday.labels : [];
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

// ═══════════════════════════════════════════════════════════════ OPTIONS TAB ═

async function loadOptions(symbol, forceRefresh) {
  currentOptionsSym = symbol;

  document.querySelectorAll(".btn-instrument").forEach(function(b) { b.classList.remove("active"); });
  const activeBtn = document.getElementById("inst-" + symbol);
  if (activeBtn) activeBtn.classList.add("active");

  if (forceRefresh) {
    await fetch("/api/cache", { method: "DELETE" });
  }

  hideEl("options-result");
  hideEl("options-error");
  showEl("options-loading");

  try {
    const r = await fetch("/api/options?symbol=" + symbol);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();

    renderOptionsResult(d);
    hideEl("options-loading");
    showEl("options-result");
  } catch (e) {
    console.error("Options error:", e);
    hideEl("options-loading");
    showEl("options-error");
  }
}

function renderOptionsResult(d) {
  const banner = document.getElementById("options-signal-banner");
  if (banner) banner.className = "options-signal-banner mb-4 " + d.signal;

  setEl("options-instrument-name", d.symbol + (d.spot ? " — ₹" + fmt(d.spot) : ""));
  setEl("options-spot-price",  d.spot ? "Spot Price: ₹" + fmt(d.spot) : "Spot unavailable");
  setEl("options-signal-label", (d.signal_emoji||"") + " " + d.signal);
  setEl("options-expiry",       "Expiry: " + (d.expiry||"N/A"));
  setEl("options-explanation",  d.explanation||"");

  // PCR sub-label uses updated thresholds (1.3/0.7 for indices)
  var pcrSub = "🟡 Neutral";
  if (d.pcr != null) {
    pcrSub = d.pcr > 1.3 ? "🟢 Bullish" : (d.pcr < 0.7 ? "🔴 Bearish" : "🟡 Neutral");
  }

  // IV Percentile card
  var ivPctVal = "—", ivPctSub = "Building history…";
  if (d.iv_percentile != null) {
    ivPctVal = d.iv_percentile.toFixed(0) + "%";
    if      (d.iv_percentile > 80) ivPctSub = "🔴 Very High — sell premium";
    else if (d.iv_percentile > 60) ivPctSub = "🟡 Elevated";
    else if (d.iv_percentile < 20) ivPctSub = "🟢 Very Low — buy options";
    else if (d.iv_percentile < 40) ivPctSub = "🟢 Below Average";
    else                           ivPctSub = "🟡 Normal";
  }

  const metrics = [
    { v: d.pcr != null ? d.pcr.toFixed(2) : "—",               l: "Put-Call Ratio (PCR)",   sub: pcrSub },
    { v: d.avg_iv != null ? d.avg_iv + "%" : "—",               l: "Avg Implied Volatility", sub: d.avg_iv > 25 ? "🔴 High" : (d.avg_iv < 15 ? "🟢 Low" : "🟡 Normal") },
    { v: ivPctVal,                                               l: "IV Percentile (30d)",    sub: ivPctSub },
    { v: d.max_pain != null ? "₹" + fmt(d.max_pain) : "—",      l: "Max Pain Strike",        sub: "Magnetic level" },
    { v: d.atm_strike != null ? "₹" + fmt(d.atm_strike) : "—",  l: "ATM Strike",             sub: "At The Money" },
    { v: fmtVol(d.total_call_oi),                                l: "Total Call OI",          sub: "Open Interest" },
    { v: fmtVol(d.total_put_oi),                                 l: "Total Put OI",           sub: "Open Interest" },
  ];

  const metricsEl = document.getElementById("options-metrics");
  if (metricsEl) metricsEl.innerHTML = metrics.map(function(m) {
    return '<div class="col-6 col-md-4"><div class="stat-box">'
      + '<div class="stat-val">' + m.v + '</div>'
      + '<div class="stat-lbl">' + m.l + '</div>'
      + '<div class="text-muted" style="font-size:.75rem">' + (m.sub||"") + '</div>'
      + '</div></div>';
  }).join("");

  const rEl = document.getElementById("options-reasons");
  if (rEl) rEl.innerHTML = (d.reasons||[]).map(function(r) { return "<li>" + r + "</li>"; }).join("");

  const lbl = document.getElementById("options-chain-label");
  if (lbl) lbl.textContent = "Expiry: " + (d.expiry||"N/A") + " · " + (d.chain ? d.chain.length : 0) + " strikes";

  renderChainTable(d.chain || []);
}

// ── Greeks toggle ────────────────────────────────────────────────────────────
function toggleGreeks() {
  var btn    = document.getElementById("greeks-toggle-btn");
  var active = btn && btn.getAttribute("data-active") === "1";
  if (btn) {
    btn.setAttribute("data-active", active ? "0" : "1");
    btn.innerHTML = active
      ? '<i class="bi bi-calculator me-1"></i>Show Greeks &amp; OI Change'
      : '<i class="bi bi-eye-slash me-1"></i>Hide Greeks';
  }
  document.querySelectorAll(".greek-col, .oi-change-col").forEach(function(el) {
    el.style.display = active ? "" : "table-cell";
  });
}

// ── Greeks / OI-change helpers ────────────────────────────────────────────────
function fmtDelta(d) {
  if (d == null) return '<span class="text-muted">—</span>';
  var cls = d >= 0 ? "delta-pos" : "delta-neg";
  return '<span class="' + cls + '">' + d.toFixed(2) + '</span>';
}
function fmtTheta(t) {
  if (t == null) return '<span class="text-muted">—</span>';
  return '<span class="theta-val">' + t.toFixed(1) + '</span>';
}
function fmtOIChange(chg) {
  if (chg == null || chg === 0) return '<span class="text-muted">—</span>';
  var cls = chg > 0 ? "oi-build" : "oi-unwind";
  var arrow = chg > 0 ? "+" : "";
  return '<span class="' + cls + '">' + arrow + fmtVol(chg) + '</span>';
}

function renderChainTable(chain) {
  const tbody = document.getElementById("options-chain-body");
  if (!tbody) return;

  if (!chain.length) {
    tbody.innerHTML = '<tr><td colspan="13" class="text-center text-muted py-4">No chain data available.</td></tr>';
    return;
  }

  const maxCOI = Math.max.apply(null, chain.map(function(r) { return r.call_oi || 0; }).concat([1]));
  const maxPOI = Math.max.apply(null, chain.map(function(r) { return r.put_oi  || 0; }).concat([1]));

  tbody.innerHTML = chain.map(function(row) {
    const atmCls   = row.is_atm ? "atm-row" : "";
    const strikeCl = row.is_atm ? "strike-cell" : "";
    const callBar  = oiBar(row.call_oi, maxCOI, "call");
    const putBar   = oiBar(row.put_oi,  maxPOI, "put");

    return '<tr class="' + atmCls + '">'
      + '<td class="call-col">'                      + callBar + '</td>'
      + '<td class="call-col oi-change-col">'        + fmtOIChange(row.call_oi_change) + '</td>'
      + '<td class="call-col">'                      + (row.call_ltp != null ? "₹" + row.call_ltp.toFixed(2) : "—") + '</td>'
      + '<td class="call-col">'                      + (row.call_iv  != null ? row.call_iv + "%" : "—") + '</td>'
      + '<td class="call-col greek-col">'            + fmtDelta(row.call_delta) + '</td>'
      + '<td class="call-col greek-col">'            + fmtTheta(row.call_theta) + '</td>'
      + '<td class="strike-col ' + strikeCl + '">₹' + fmt(row.strike) + (row.is_atm ? " ★" : "") + '</td>'
      + '<td class="put-col greek-col">'             + fmtTheta(row.put_theta) + '</td>'
      + '<td class="put-col greek-col">'             + fmtDelta(row.put_delta) + '</td>'
      + '<td class="put-col">'                       + (row.put_iv   != null ? row.put_iv  + "%" : "—") + '</td>'
      + '<td class="put-col">'                       + (row.put_ltp  != null ? "₹" + row.put_ltp.toFixed(2) : "—") + '</td>'
      + '<td class="put-col oi-change-col">'         + fmtOIChange(row.put_oi_change) + '</td>'
      + '<td class="put-col">'                       + putBar + '</td>'
      + '</tr>';
  }).join("");
}

function oiBar(oi, maxOI, side) {
  if (!oi) return '<span class="text-muted">0</span>';
  const pct = Math.min(100, Math.round((oi / maxOI) * 100));
  return '<div class="oi-bar"><span>' + fmtVol(oi) + '</span>'
    + '<div class="oi-bar-bg"><div class="oi-bar-fill ' + side + '" style="width:' + pct + '%"></div></div></div>';
}

// ═══════════════════════════════════════════════════════════════ WISHLIST TAB ═

async function loadWishlistSymbols() {
  try {
    const r = await fetch("/api/wishlist");
    if (!r.ok) return;
    const d = await r.json();
    wishlistSymbols = new Set((d.stocks||[]).map(function(s) { return s.symbol; }));
    updateWishlistBadge(d.stocks ? d.stocks.length : 0);
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

    hideEl("wishlist-loading");
    const stocks = d.stocks || [];
    wishlistSymbols = new Set(stocks.map(function(s) { return s.symbol; }));
    updateWishlistBadge(stocks.length);
    setEl("wishlist-count", stocks.length);

    if (!stocks.length) {
      showEl("wishlist-empty");
      return;
    }

    if (grid) grid.innerHTML = stocks.map(function(s) { return stockCard(s, true); }).join("");
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
  countdownSecs = 300;
  const txt = document.getElementById("countdown");
  const bar = document.getElementById("refresh-progress");

  if (countdownTimer) clearInterval(countdownTimer);

  countdownTimer = setInterval(function() {
    countdownSecs--;
    if (txt) txt.textContent = countdownSecs;
    if (bar) bar.style.width = ((300 - countdownSecs) / 300 * 100) + "%";

    if (countdownSecs <= 0) {
      countdownSecs = 300;
      loadStocks(true);
      if (currentTab === "options") loadOptions(currentOptionsSym, true);
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
