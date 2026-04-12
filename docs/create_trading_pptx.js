const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

const {
  FaRocket, FaStar, FaChartLine, FaBrain, FaServer, FaComments,
  FaWallet, FaCode, FaDollarSign, FaStripeLine, FaTachometerAlt,
  FaCheckCircle, FaTimesCircle, FaExclamationTriangle, FaInfoCircle,
  FaDatabase, FaCloud, FaBolt, FaLock, FaSearch, FaArrowRight,
  FaEye, FaFilter, FaShieldAlt, FaChartBar, FaTrophy, FaWrench,
  FaGlobe, FaLayerGroup, FaSyncAlt, FaCog
} = require("react-icons/fa");

// ─── COLOR PALETTE ───
const C = {
  navy:      "1E2761",
  deepNavy:  "141B3D",
  midBlue:   "2E4DA7",
  accentCyan:"3EC6E0",
  white:     "FFFFFF",
  ice:       "CADCFC",
  lightBg:   "1A2456",
  cardBg:    "243070",
  darkCard:  "0D1533",
  green:     "2ECC71",
  red:       "E74C3C",
  amber:     "F39C12",
  mutedText: "8BA3CC",
};

// ─── HELPERS ───
function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

const mkShadow = () => ({ type: "outer", color: "000000", blur: 10, offset: 4, angle: 135, opacity: 0.25 });
const mkCardShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.20 });

// ─── COMMON SLIDE ELEMENTS ───
function addSlideHeader(slide, pres, title) {
  // Dark top bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.7,
    fill: { color: C.deepNavy }
  });
  // Cyan left accent
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.12, h: 0.7,
    fill: { color: C.accentCyan }
  });
  slide.addText(title, {
    x: 0.3, y: 0, w: 9.4, h: 0.7,
    fontSize: 22, fontFace: "Calibri", color: C.white, bold: true,
    valign: "middle", margin: 0
  });
}

async function createPresentation() {
  let pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Arya Kirti Singh";
  pres.title = "AI Trading Assistant";

  // Pre-render icons
  const icons = {};
  const iconDefs = {
    rocket:   [FaRocket,   "#" + C.accentCyan],
    star:     [FaStar,     "#" + C.accentCyan],
    chart:    [FaChartLine,"#" + C.accentCyan],
    brain:    [FaBrain,    "#" + C.accentCyan],
    server:   [FaServer,   "#" + C.accentCyan],
    chat:     [FaComments, "#" + C.accentCyan],
    wallet:   [FaWallet,   "#" + C.accentCyan],
    code:     [FaCode,     "#" + C.accentCyan],
    dollar:   [FaDollarSign,"#" + C.accentCyan],
    gauge:    [FaTachometerAlt,"#" + C.accentCyan],
    check:    [FaCheckCircle,"#" + C.green],
    times:    [FaTimesCircle,"#" + C.red],
    warn:     [FaExclamationTriangle,"#" + C.amber],
    info:     [FaInfoCircle,"#" + C.accentCyan],
    db:       [FaDatabase, "#" + C.accentCyan],
    cloud:    [FaCloud,    "#" + C.accentCyan],
    bolt:     [FaBolt,     "#" + C.amber],
    lock:     [FaLock,     "#" + C.accentCyan],
    search:   [FaSearch,   "#" + C.accentCyan],
    arrow:    [FaArrowRight,"#" + C.white],
    eye:      [FaEye,      "#" + C.accentCyan],
    filter:   [FaFilter,   "#" + C.accentCyan],
    shield:   [FaShieldAlt,"#" + C.accentCyan],
    bar:      [FaChartBar, "#" + C.accentCyan],
    trophy:   [FaTrophy,   "#" + C.amber],
    wrench:   [FaWrench,   "#" + C.amber],
    globe:    [FaGlobe,    "#" + C.accentCyan],
    layers:   [FaLayerGroup,"#" + C.accentCyan],
    sync:     [FaSyncAlt,  "#" + C.accentCyan],
    cog:      [FaCog,      "#" + C.accentCyan],
    // White versions
    rocketW:  [FaRocket,   "#" + C.white],
    chartW:   [FaChartLine,"#" + C.white],
    checkW:   [FaCheckCircle,"#" + C.white],
    brainW:   [FaBrain,    "#" + C.white],
    globeW:   [FaGlobe,    "#" + C.white],
    boltW:    [FaBolt,     "#" + C.white],
    warnW:    [FaExclamationTriangle,"#" + C.white],
    cogW:     [FaCog,      "#" + C.white],
  };

  for (const [key, [Icon, color]] of Object.entries(iconDefs)) {
    icons[key] = await iconToBase64Png(Icon, color);
  }

  // ════════════════════════════════════════════
  // SLIDE 1: TITLE
  // ════════════════════════════════════════════
  let s1 = pres.addSlide();
  s1.background = { color: C.deepNavy };

  // Decorative blobs
  s1.addShape(pres.shapes.OVAL, { x: 6.5, y: -1, w: 5, h: 5, fill: { color: C.midBlue, transparency: 55 } });
  s1.addShape(pres.shapes.OVAL, { x: 7.5, y: 1.5, w: 3.5, h: 3.5, fill: { color: C.accentCyan, transparency: 75 } });
  // Bottom cyan bar
  s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.15, w: 10, h: 0.475, fill: { color: C.accentCyan } });

  s1.addImage({ data: icons.chart, x: 0.7, y: 0.8, w: 0.65, h: 0.65 });
  s1.addText("AI Trading Assistant", {
    x: 0.7, y: 1.55, w: 8, h: 1.0,
    fontSize: 40, fontFace: "Calibri", color: C.white, bold: true,
    lineSpacingMultiple: 1.1, margin: 0
  });
  s1.addText("Intelligent Intraday Signals  |  AI Chat  |  Portfolio Management", {
    x: 0.7, y: 2.65, w: 8, h: 0.45,
    fontSize: 16, fontFace: "Calibri", color: C.accentCyan, italic: true, margin: 0
  });
  s1.addText("Built on AWS Lambda + Bedrock + Streamlit", {
    x: 0.7, y: 3.25, w: 7, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.ice, margin: 0
  });
  s1.addText("Arya Kirti Singh  |  2024", {
    x: 0.7, y: 4.2, w: 7, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.mutedText, margin: 0
  });

  // ════════════════════════════════════════════
  // SLIDE 2: WHY I BUILT THIS
  // ════════════════════════════════════════════
  let s2 = pres.addSlide();
  s2.background = { color: C.navy };
  addSlideHeader(s2, pres, "Why I Built This");

  const whyItems = [
    { icon: icons.search, title: "Signal Noise", desc: "Manual scanning of 200+ stocks daily was slow and unreliable — needed automated intelligence" },
    { icon: icons.bolt, title: "Missed Entries", desc: "By the time patterns were spotted, the optimal entry window had often closed" },
    { icon: icons.brain, title: "AI-Powered Edge", desc: "Combine 12 technical indicators with Bedrock AI validation for higher-confidence signals" },
    { icon: icons.dollar, title: "Risk Discipline", desc: "Built-in R:R ratio enforcement — never enter a trade without knowing the risk/reward upfront" },
  ];

  whyItems.forEach((item, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const cx = 0.5 + col * 4.9;
    const cy = 0.95 + row * 2.1;

    s2.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 4.4, h: 1.8, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    // Cyan top accent on card
    s2.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 4.4, h: 0.07, fill: { color: C.accentCyan } });

    // Icon circle
    s2.addShape(pres.shapes.OVAL, { x: cx + 0.25, y: cy + 0.3, w: 0.55, h: 0.55, fill: { color: C.navy } });
    s2.addImage({ data: item.icon, x: cx + 0.32, y: cy + 0.37, w: 0.41, h: 0.41 });

    s2.addText(item.title, {
      x: cx + 0.95, y: cy + 0.25, w: 3.3, h: 0.4,
      fontSize: 15, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    s2.addText(item.desc, {
      x: cx + 0.95, y: cy + 0.65, w: 3.3, h: 1.0,
      fontSize: 12, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // ════════════════════════════════════════════
  // SLIDE 3: KEY FEATURES
  // ════════════════════════════════════════════
  let s3 = pres.addSlide();
  s3.background = { color: C.navy };
  addSlideHeader(s3, pres, "Key Features");

  const features = [
    { icon: icons.chartW, color: C.midBlue, title: "Signal Engine", desc: "12 indicators: RSI, MACD, BB, ATR, OBV, Stoch, ADX, MFI, VWAP, EMA, SMA, RS" },
    { icon: icons.brainW, color: "1A7A5E", title: "AI Validation", desc: "Claude Haiku validates every signal — confirms or rejects with reasoning & confidence score" },
    { icon: icons.globeW, color: "6B3A9E", title: "Index Strip", desc: "NIFTY 50, BANKNIFTY, VIX always visible — live prices via direct Yahoo Finance v8 API" },
    { icon: icons.cogW, color: "8B4A1A", title: "Portfolio Tools", desc: "Personal watchlist, trade log, performance metrics — all isolated per Cognito user" },
    { icon: icons.boltW, color: "1A5C8B", title: "Real-time Data", desc: "AWS Lambda pulls live quotes, processes signals, stores results in DynamoDB" },
    { icon: icons.checkW, color: "5A1A6E", title: "R:R Badges", desc: "Every stock card shows Risk:Reward ratio — colour-coded green/amber/red for quick decisions" },
  ];

  const cols = 3;
  const boxW = 2.95;
  const boxH = 1.5;
  const gapX = 0.15;
  const gapY = 0.25;
  const startX = 0.4;
  const startY = 0.85;

  features.forEach((f, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const fx = startX + col * (boxW + gapX);
    const fy = startY + row * (boxH + gapY);

    s3.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy, w: boxW, h: boxH, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    // Color stripe top
    s3.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy, w: boxW, h: 0.08, fill: { color: f.color } });
    // Icon circle
    s3.addShape(pres.shapes.OVAL, { x: fx + 0.2, y: fy + 0.2, w: 0.5, h: 0.5, fill: { color: f.color } });
    s3.addImage({ data: f.icon, x: fx + 0.27, y: fy + 0.27, w: 0.36, h: 0.36 });

    s3.addText(f.title, {
      x: fx + 0.85, y: fy + 0.18, w: boxW - 1.0, h: 0.38,
      fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    s3.addText(f.desc, {
      x: fx + 0.2, y: fy + 0.72, w: boxW - 0.4, h: 0.72,
      fontSize: 10.5, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // ════════════════════════════════════════════
  // SLIDE 4: SIGNAL ALGORITHM
  // ════════════════════════════════════════════
  let s4 = pres.addSlide();
  s4.background = { color: C.navy };
  addSlideHeader(s4, pres, "Signal Algorithm — 12 Indicators");

  // Left: indicator grid
  const indicators = [
    { name: "RSI", desc: "Overbought/oversold momentum" },
    { name: "MACD", desc: "Trend momentum crossover" },
    { name: "Bollinger Bands", desc: "Volatility squeeze signals" },
    { name: "ATR", desc: "True range for stop-loss sizing" },
    { name: "OBV", desc: "Volume confirms price moves" },
    { name: "Stochastic", desc: "K/D oscillator divergence" },
    { name: "ADX", desc: "Trend strength filter (>25)" },
    { name: "MFI", desc: "Money Flow Index" },
    { name: "VWAP", desc: "Volume-weighted anchor" },
    { name: "EMA 9/21", desc: "Short-term trend direction" },
    { name: "SMA 50/200", desc: "Long-term trend regime" },
    { name: "RS Ratio", desc: "(1+stock)/(1+nifty) vs benchmark" },
  ];

  const iCols = 2;
  const iW = 3.1;
  const iH = 0.42;
  const iGapX = 0.2;
  const iGapY = 0.08;
  const iStartX = 0.35;
  const iStartY = 0.82;

  indicators.forEach((ind, i) => {
    const col = i % iCols;
    const row = Math.floor(i / iCols);
    const ix = iStartX + col * (iW + iGapX);
    const iy = iStartY + row * (iH + iGapY);

    s4.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: iW, h: iH, fill: { color: C.lightBg } });
    s4.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: 0.06, h: iH, fill: { color: C.accentCyan } });
    s4.addText(ind.name, {
      x: ix + 0.15, y: iy + 0.02, w: 1.2, h: 0.38,
      fontSize: 11, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0, valign: "middle"
    });
    s4.addText(ind.desc, {
      x: ix + 1.35, y: iy + 0.02, w: 1.7, h: 0.38,
      fontSize: 9.5, fontFace: "Calibri", color: C.mutedText, margin: 0, valign: "middle"
    });
  });

  // Right: scoring panel
  const rpX = 6.95;
  s4.addShape(pres.shapes.RECTANGLE, { x: rpX, y: 0.82, w: 2.7, h: 4.55, fill: { color: C.lightBg }, shadow: mkShadow() });
  s4.addShape(pres.shapes.RECTANGLE, { x: rpX, y: 0.82, w: 2.7, h: 0.06, fill: { color: C.accentCyan } });

  s4.addText("Scoring Logic", {
    x: rpX + 0.15, y: 0.9, w: 2.4, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, margin: 0
  });

  const scoringItems = [
    { score: "8-12", label: "STRONG BUY", color: "27AE60" },
    { score: "5-7",  label: "BUY",         color: "2ECC71" },
    { score: "3-4",  label: "HOLD",         color: C.amber },
    { score: "1-2",  label: "SELL",         color: "E67E22" },
    { score: "0",    label: "STRONG SELL",  color: C.red },
  ];

  scoringItems.forEach((s, i) => {
    const sy = 1.45 + i * 0.62;
    s4.addShape(pres.shapes.RECTANGLE, { x: rpX + 0.15, y: sy, w: 2.4, h: 0.52, fill: { color: C.navy } });
    s4.addShape(pres.shapes.RECTANGLE, { x: rpX + 0.15, y: sy, w: 0.06, h: 0.52, fill: { color: s.color } });
    s4.addText(s.score + " pts", {
      x: rpX + 0.3, y: sy, w: 0.75, h: 0.52,
      fontSize: 14, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0, valign: "middle"
    });
    s4.addText(s.label, {
      x: rpX + 1.1, y: sy, w: 1.5, h: 0.52,
      fontSize: 11, fontFace: "Calibri", color: s.color, bold: true, margin: 0, valign: "middle"
    });
  });

  s4.addText("+ AI Validation (Bedrock Claude Haiku)\nconfidence score added to final rank", {
    x: rpX + 0.15, y: 4.6, w: 2.4, h: 0.6,
    fontSize: 9.5, fontFace: "Calibri", color: C.mutedText, margin: 0, italic: true
  });

  // ════════════════════════════════════════════
  // SLIDE 5: ARCHITECTURE
  // ════════════════════════════════════════════
  let s5 = pres.addSlide();
  s5.background = { color: C.navy };
  addSlideHeader(s5, pres, "Architecture");

  const archLayers = [
    {
      y: 0.85, color: C.midBlue, label: "Frontend", icon: icons.globeW,
      items: ["Streamlit UI", "Index Strip (NIFTY/BANKNIFTY/VIX)", "Signal Dashboard", "AI Chat", "Portfolio"]
    },
    {
      y: 2.05, color: "1A7A5E", label: "AWS Lambda", icon: icons.boltW,
      items: ["Signal Engine (12 indicators)", "AI Validator (Bedrock Haiku)", "Sentiment Agent (Nova Micro)", "Yahoo Finance v8 API"]
    },
    {
      y: 3.25, color: "6B3A9E", label: "Data Layer", icon: icons.cogW,
      items: ["DynamoDB — signals & portfolio", "S3 — historical data cache", "Cognito — JWT auth, per-user isolation", "EventBridge — scheduled triggers"]
    },
  ];

  archLayers.forEach(layer => {
    s5.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: layer.y, w: 9.3, h: 1.0, fill: { color: layer.color, transparency: 15 }, shadow: mkCardShadow() });
    // Left icon area
    s5.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: layer.y, w: 1.5, h: 1.0, fill: { color: layer.color } });
    s5.addImage({ data: layer.icon, x: 0.63, y: layer.y + 0.22, w: 0.45, h: 0.45 });
    s5.addText(layer.label, {
      x: 0.38, y: layer.y + 0.65, w: 1.45, h: 0.28,
      fontSize: 9, fontFace: "Calibri", color: C.white, bold: true, align: "center", margin: 0
    });

    // Items as pills
    layer.items.forEach((item, j) => {
      const px = 2.0 + j * 1.82;
      s5.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px, y: layer.y + 0.25, w: 1.7, h: 0.5, fill: { color: C.navy }, rectRadius: 0.08 });
      s5.addText(item, {
        x: px + 0.07, y: layer.y + 0.27, w: 1.56, h: 0.46,
        fontSize: 8.5, fontFace: "Calibri", color: C.white, align: "center", valign: "middle", margin: 0
      });
    });
  });

  // Auth callout
  s5.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 4.45, w: 9.3, h: 0.85, fill: { color: C.deepNavy }, shadow: mkCardShadow() });
  s5.addImage({ data: icons.lock, x: 0.6, y: 4.65, w: 0.45, h: 0.45 });
  s5.addText("Auth & Security: ", {
    x: 1.15, y: 4.45, w: 1.5, h: 0.85,
    fontSize: 12, fontFace: "Calibri", color: C.accentCyan, bold: true, valign: "middle", margin: 0
  });
  s5.addText("Cognito JWT tokens — per-user DynamoDB isolation. Email verification required. All Lambda calls are signed AWS API requests.", {
    x: 2.65, y: 4.45, w: 6.8, h: 0.85,
    fontSize: 11, fontFace: "Calibri", color: C.mutedText, valign: "middle", margin: 0
  });

  // ════════════════════════════════════════════
  // SLIDE 6: AI CHAT
  // ════════════════════════════════════════════
  let s6 = pres.addSlide();
  s6.background = { color: C.navy };
  addSlideHeader(s6, pres, "AI Chat — Ask the Market");

  // Mock chat UI
  const chatMessages = [
    { who: "You", msg: "Why is RELIANCE showing a STRONG BUY?", side: "right", color: C.midBlue },
    { who: "AI", msg: "RELIANCE is up 2.3% on OBV surge with RSI at 58 (momentum). MACD crossed bullish 3 bars ago. RS Ratio vs NIFTY is 1.04 — outperforming. Entry: 2847, Target: 2940, Stop: 2800.", side: "left", color: C.lightBg },
    { who: "You", msg: "What's the market sentiment today?", side: "right", color: C.midBlue },
    { who: "AI", msg: "NIFTY +0.8% | BANKNIFTY +1.1% | VIX 13.2 (calm). 68% of scanned stocks show bullish bias. Sector leaders: IT, Banking.", side: "left", color: C.lightBg },
  ];

  chatMessages.forEach((msg, i) => {
    const isRight = msg.side === "right";
    const bw = 5.5;
    const bx = isRight ? 10 - 0.4 - bw : 0.4;
    const by = 0.9 + i * 1.05;

    s6.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: by, w: bw, h: 0.9, fill: { color: msg.color }, rectRadius: 0.12 });
    s6.addText(msg.who + ":", {
      x: bx + 0.18, y: by + 0.05, w: bw - 0.3, h: 0.25,
      fontSize: 9.5, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0
    });
    s6.addText(msg.msg, {
      x: bx + 0.18, y: by + 0.28, w: bw - 0.3, h: 0.58,
      fontSize: 10.5, fontFace: "Calibri", color: C.white, margin: 0
    });
  });

  // Right panel: capabilities
  s6.addShape(pres.shapes.RECTANGLE, { x: 6.0, y: 0.85, w: 3.65, h: 4.5, fill: { color: C.lightBg }, shadow: mkShadow() });
  s6.addText("Capabilities", {
    x: 6.2, y: 0.95, w: 3.2, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0
  });

  const chatCaps = [
    "Signal explanations with indicator breakdown",
    "Market context using index strip data",
    "Portfolio analysis & trade reviews",
    "Risk assessment per position",
    "Bedrock Claude 3.5 Sonnet backbone",
    "Cognito-isolated chat history per user",
  ];
  chatCaps.forEach((cap, i) => {
    s6.addImage({ data: icons.check, x: 6.2, y: 1.5 + i * 0.55, w: 0.28, h: 0.28 });
    s6.addText(cap, {
      x: 6.55, y: 1.5 + i * 0.55, w: 2.95, h: 0.4,
      fontSize: 11, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // ════════════════════════════════════════════
  // SLIDE 7: PORTFOLIO & WISHLIST
  // ════════════════════════════════════════════
  let s7 = pres.addSlide();
  s7.background = { color: C.navy };
  addSlideHeader(s7, pres, "Portfolio & Wishlist");

  // Two columns
  const sections = [
    {
      x: 0.35, title: "Portfolio Tracker", icon: icons.wallet, color: C.midBlue,
      items: [
        "Log trades with entry price, quantity, date",
        "Live P&L calculated against current price",
        "Per-trade return % and absolute gain/loss",
        "CSV export for tax/reconciliation",
        "All data isolated per Cognito user",
      ]
    },
    {
      x: 5.15, title: "Wishlist (Watchlist)", icon: icons.star, color: "6B3A9E",
      items: [
        "Add any NSE stock to personal watchlist",
        "Live signal updates every 5 minutes",
        "Quick-access from main dashboard",
        "Wishlist signals trigger push summary",
        "Per-user isolation via JWT",
      ]
    }
  ];

  sections.forEach(sec => {
    s7.addShape(pres.shapes.RECTANGLE, { x: sec.x, y: 0.85, w: 4.6, h: 4.5, fill: { color: C.lightBg }, shadow: mkShadow() });
    s7.addShape(pres.shapes.RECTANGLE, { x: sec.x, y: 0.85, w: 4.6, h: 0.07, fill: { color: sec.color } });

    s7.addShape(pres.shapes.OVAL, { x: sec.x + 0.2, y: 1.0, w: 0.55, h: 0.55, fill: { color: sec.color } });
    s7.addImage({ data: sec.icon, x: sec.x + 0.27, y: 1.06, w: 0.41, h: 0.41 });

    s7.addText(sec.title, {
      x: sec.x + 0.9, y: 1.0, w: 3.5, h: 0.5,
      fontSize: 16, fontFace: "Calibri", color: C.white, bold: true, margin: 0, valign: "middle"
    });

    sec.items.forEach((item, j) => {
      s7.addImage({ data: icons.check, x: sec.x + 0.25, y: 1.72 + j * 0.6, w: 0.28, h: 0.28 });
      s7.addText(item, {
        x: sec.x + 0.65, y: 1.72 + j * 0.6, w: 3.8, h: 0.45,
        fontSize: 12, fontFace: "Calibri", color: C.mutedText, margin: 0
      });
    });
  });

  // ════════════════════════════════════════════
  // SLIDE 8: TECH STACK
  // ════════════════════════════════════════════
  let s8 = pres.addSlide();
  s8.background = { color: C.navy };
  addSlideHeader(s8, pres, "Tech Stack");

  const stackLayers = [
    {
      label: "Frontend", color: C.midBlue,
      techs: ["Streamlit", "Python 3.11", "Plotly", "Boto3 SDK"]
    },
    {
      label: "Compute", color: "1A7A5E",
      techs: ["AWS Lambda", "Python 3.11", "yfinance / Yahoo v8 API", "pandas / numpy"]
    },
    {
      label: "AI / ML", color: "6B3A9E",
      techs: ["Bedrock Claude 3.5 Sonnet", "Claude Haiku (validator)", "Nova Micro (sentiment)", "Prompt templates"]
    },
    {
      label: "Data & Auth", color: "8B4A1A",
      techs: ["DynamoDB", "S3", "Cognito (JWT)", "EventBridge cron"]
    },
    {
      label: "Infra / CI", color: "1A5C8B",
      techs: ["Terraform (IaC)", "GitHub Actions", "Lambda layers", "CloudWatch logs"]
    },
  ];

  stackLayers.forEach((layer, i) => {
    const sy = 0.88 + i * 0.92;
    s8.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: sy, w: 1.4, h: 0.78, fill: { color: layer.color } });
    s8.addText(layer.label, {
      x: 0.35, y: sy, w: 1.4, h: 0.78,
      fontSize: 11, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
    s8.addShape(pres.shapes.RECTANGLE, { x: 1.75, y: sy, w: 8.0, h: 0.78, fill: { color: C.lightBg } });

    layer.techs.forEach((tech, j) => {
      const tx = 2.0 + j * 2.0;
      s8.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: tx, y: sy + 0.14, w: 1.75, h: 0.5, fill: { color: C.navy }, rectRadius: 0.08 });
      s8.addText(tech, {
        x: tx + 0.08, y: sy + 0.14, w: 1.59, h: 0.5,
        fontSize: 9.5, fontFace: "Calibri", color: C.white, align: "center", valign: "middle", margin: 0
      });
    });
  });

  // ════════════════════════════════════════════
  // SLIDE 9: COST & SCALABILITY
  // ════════════════════════════════════════════
  let s9 = pres.addSlide();
  s9.background = { color: C.navy };
  addSlideHeader(s9, pres, "Cost & Scalability");

  // Stat callouts row
  const stats = [
    { val: "~$3", label: "per month\nAWS cost", color: C.accentCyan },
    { val: "<3s", label: "Lambda cold\nstart p95", color: "2ECC71" },
    { val: "200+", label: "stocks scanned\nper cycle", color: C.amber },
    { val: "5 min", label: "signal refresh\ncadence", color: "A78BFA" },
  ];

  stats.forEach((stat, i) => {
    const sx = 0.5 + i * 2.3;
    s9.addShape(pres.shapes.RECTANGLE, { x: sx, y: 0.88, w: 2.0, h: 1.5, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    s9.addShape(pres.shapes.RECTANGLE, { x: sx, y: 0.88, w: 2.0, h: 0.07, fill: { color: stat.color } });
    s9.addText(stat.val, {
      x: sx, y: 1.0, w: 2.0, h: 0.75,
      fontSize: 36, fontFace: "Calibri", color: stat.color, bold: true, align: "center", margin: 0
    });
    s9.addText(stat.label, {
      x: sx, y: 1.78, w: 2.0, h: 0.52,
      fontSize: 10, fontFace: "Calibri", color: C.mutedText, align: "center", margin: 0
    });
  });

  // Scalability notes
  const scaleItems = [
    { icon: icons.cloud, title: "Serverless by design", desc: "Lambda + DynamoDB auto-scales — no idle EC2 costs. Pay only per invocation." },
    { icon: icons.db,    title: "DynamoDB on-demand", desc: "No capacity planning. Handles 1 user or 1,000 users with same infrastructure." },
    { icon: icons.sync,  title: "Scheduled scans", desc: "EventBridge cron triggers Lambda every 5 min during market hours (9:15–15:30 IST)." },
    { icon: icons.shield, title: "Cost ceiling", desc: "Free tier covers most usage. AWS Budgets alert set at $10/month threshold." },
  ];

  scaleItems.forEach((item, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const ix = 0.5 + col * 4.8;
    const iy = 2.65 + row * 1.3;

    s9.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: 4.3, h: 1.1, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    s9.addShape(pres.shapes.OVAL, { x: ix + 0.18, y: iy + 0.28, w: 0.52, h: 0.52, fill: { color: C.navy } });
    s9.addImage({ data: item.icon, x: ix + 0.25, y: iy + 0.35, w: 0.38, h: 0.38 });
    s9.addText(item.title, {
      x: ix + 0.85, y: iy + 0.08, w: 3.3, h: 0.38,
      fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    s9.addText(item.desc, {
      x: ix + 0.85, y: iy + 0.48, w: 3.3, h: 0.55,
      fontSize: 10.5, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // ════════════════════════════════════════════
  // SLIDE A: LIVE MARKET INTELLIGENCE STRIP
  // ════════════════════════════════════════════
  let sA = pres.addSlide();
  sA.background = { color: C.navy };
  addSlideHeader(sA, pres, "Live Market Intelligence Strip");

  // Mock index strip at top
  sA.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.75, fill: { color: C.deepNavy }, shadow: mkShadow() });

  // NIFTY pill
  sA.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.55, y: 0.95, w: 2.7, h: 0.55, fill: { color: C.navy }, rectRadius: 0.08 });
  sA.addText("NIFTY 50", { x: 0.65, y: 0.97, w: 0.9, h: 0.22, fontSize: 8, fontFace: "Calibri", color: C.mutedText, bold: true, margin: 0 });
  sA.addText("24,531.50", { x: 0.65, y: 1.18, w: 0.9, h: 0.24, fontSize: 10, fontFace: "Calibri", color: C.white, bold: true, margin: 0 });
  sA.addText("+0.82%", { x: 1.6, y: 0.97, w: 1.5, h: 0.51, fontSize: 13, fontFace: "Calibri", color: "2ECC71", bold: true, valign: "middle", margin: 0 });

  // BANKNIFTY pill
  sA.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 3.45, y: 0.95, w: 2.8, h: 0.55, fill: { color: C.navy }, rectRadius: 0.08 });
  sA.addText("BANKNIFTY", { x: 3.55, y: 0.97, w: 1.15, h: 0.22, fontSize: 8, fontFace: "Calibri", color: C.mutedText, bold: true, margin: 0 });
  sA.addText("52,140.30", { x: 3.55, y: 1.18, w: 1.15, h: 0.24, fontSize: 10, fontFace: "Calibri", color: C.white, bold: true, margin: 0 });
  sA.addText("+1.14%", { x: 4.75, y: 0.97, w: 1.4, h: 0.51, fontSize: 13, fontFace: "Calibri", color: "2ECC71", bold: true, valign: "middle", margin: 0 });

  // VIX pill (red — fear)
  sA.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.45, y: 0.95, w: 2.0, h: 0.55, fill: { color: C.navy }, rectRadius: 0.08 });
  sA.addText("INDIA VIX", { x: 6.55, y: 0.97, w: 0.9, h: 0.22, fontSize: 8, fontFace: "Calibri", color: C.mutedText, bold: true, margin: 0 });
  sA.addText("13.24", { x: 6.55, y: 1.18, w: 0.9, h: 0.24, fontSize: 10, fontFace: "Calibri", color: C.white, bold: true, margin: 0 });
  sA.addText("+2.1%", { x: 7.5, y: 0.97, w: 0.85, h: 0.51, fontSize: 13, fontFace: "Calibri", color: C.red, bold: true, valign: "middle", margin: 0 });

  // Refresh badge
  sA.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.6, y: 0.97, w: 0.95, h: 0.51, fill: { color: "1A2456" }, rectRadius: 0.08 });
  sA.addText("5 min", { x: 8.6, y: 0.97, w: 0.95, h: 0.28, fontSize: 8.5, fontFace: "Calibri", color: C.accentCyan, bold: true, align: "center", margin: 0 });
  sA.addText("refresh", { x: 8.6, y: 1.22, w: 0.95, h: 0.26, fontSize: 8, fontFace: "Calibri", color: C.mutedText, align: "center", margin: 0 });

  // Feature cards below
  const stripFeatures = [
    { icon: icons.globe, title: "Always Visible", desc: "Index strip is pinned in the Streamlit header — visible on every page of the app without scrolling" },
    { icon: icons.bolt, title: "Sub-3s Response", desc: "Direct Yahoo Finance v8 API calls from Lambda — no yfinance library overhead that caused timeouts" },
    { icon: icons.eye, title: "Market-Aware Display", desc: "Shows last close price when market is closed. Switches to live price automatically during 9:15–15:30 IST trading hours" },
    { icon: icons.chart, title: "Colour-Coded Moves", desc: "% change shown in green (up) or red (down) — instant visual context without reading the numbers" },
  ];

  stripFeatures.forEach((f, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const fx = 0.35 + col * 4.8;
    const fy = 1.85 + row * 1.55;

    sA.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy, w: 4.5, h: 1.35, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    sA.addShape(pres.shapes.OVAL, { x: fx + 0.2, y: fy + 0.38, w: 0.52, h: 0.52, fill: { color: C.navy } });
    sA.addImage({ data: f.icon, x: fx + 0.27, y: fy + 0.45, w: 0.38, h: 0.38 });
    sA.addText(f.title, {
      x: fx + 0.88, y: fy + 0.15, w: 3.45, h: 0.38,
      fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    sA.addText(f.desc, {
      x: fx + 0.88, y: fy + 0.56, w: 3.45, h: 0.72,
      fontSize: 10.5, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // ════════════════════════════════════════════
  // SLIDE B: SIGNAL DASHBOARD — AT A GLANCE
  // ════════════════════════════════════════════
  let sB = pres.addSlide();
  sB.background = { color: C.navy };
  addSlideHeader(sB, pres, "Signal Dashboard — At a Glance");

  // Summary cards row
  const summaryCards = [
    { label: "STRONG BUY", count: "12", color: "27AE60" },
    { label: "BUY",         count: "28", color: "2ECC71" },
    { label: "HOLD",        count: "41", color: C.amber },
    { label: "SELL",        count: "15", color: "E67E22" },
    { label: "STRONG SELL", count: "4",  color: C.red },
    { label: "Avg AI Score", count: "7.2", color: C.accentCyan },
  ];

  summaryCards.forEach((card, i) => {
    const cx = 0.35 + i * 1.56;
    sB.addShape(pres.shapes.RECTANGLE, { x: cx, y: 0.85, w: 1.42, h: 1.3, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    sB.addShape(pres.shapes.RECTANGLE, { x: cx, y: 0.85, w: 1.42, h: 0.07, fill: { color: card.color } });
    sB.addText(card.count, {
      x: cx, y: 0.97, w: 1.42, h: 0.55,
      fontSize: 32, fontFace: "Calibri", color: card.color, bold: true, align: "center", margin: 0
    });
    sB.addText(card.label, {
      x: cx + 0.05, y: 1.58, w: 1.32, h: 0.5,
      fontSize: 8.5, fontFace: "Calibri", color: C.mutedText, align: "center", margin: 0
    });
  });

  // Top Movers Strip
  sB.addText("Top Movers", {
    x: 0.35, y: 2.32, w: 2.0, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0
  });
  const movers = [
    { sym: "IRFC", pct: "+4.2%", col: "2ECC71" },
    { sym: "POWERGRID", pct: "+3.1%", col: "2ECC71" },
    { sym: "HDFCBANK", pct: "+2.6%", col: "2ECC71" },
    { sym: "COALINDIA", pct: "-1.8%", col: C.red },
    { sym: "ADANIENT", pct: "-2.4%", col: C.red },
  ];

  sB.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 2.7, w: 9.3, h: 0.6, fill: { color: C.deepNavy } });
  movers.forEach((m, i) => {
    const mpx = 0.55 + i * 1.85;
    sB.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: mpx, y: 2.78, w: 1.65, h: 0.44, fill: { color: C.navy }, rectRadius: 0.08 });
    sB.addText(m.sym, { x: mpx + 0.08, y: 2.79, w: 0.9, h: 0.42, fontSize: 8.5, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });
    sB.addText(m.pct, { x: mpx + 0.95, y: 2.79, w: 0.65, h: 0.42, fontSize: 9.5, fontFace: "Calibri", color: m.col, bold: true, valign: "middle", margin: 0 });
  });

  // Feature cards lower half
  const dashFeatures = [
    {
      icon: icons.bar, color: C.midBlue, title: "Signal Summary Cards",
      desc: "One-line snapshot of STRONG BUY / BUY / HOLD / SELL / STRONG SELL counts + Avg AI Score at top of dashboard"
    },
    {
      icon: icons.filter, color: "1A7A5E", title: "Top Movers Strip",
      desc: "Scrolling pills showing biggest % movers always pinned above the signal grid — spot leaders instantly"
    },
    {
      icon: icons.trophy, color: "6B3A9E", title: "R:R Ratio Badge",
      desc: "Every stock card shows Risk:Reward ratio. Green badge ≥ 2:1 | Amber ≥ 1:1 | Red < 1:1"
    },
    {
      icon: icons.sync, color: "8B4A1A", title: "Signal Timestamps",
      desc: "Each signal shows when it was last computed (IST) — know if you're looking at fresh or stale data"
    },
  ];

  dashFeatures.forEach((f, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const fx = 0.35 + col * 4.8;
    const fy = 3.45 + row * 1.0;

    sB.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy, w: 4.5, h: 0.88, fill: { color: C.lightBg }, shadow: mkCardShadow() });
    sB.addShape(pres.shapes.OVAL, { x: fx + 0.15, y: fy + 0.18, w: 0.5, h: 0.5, fill: { color: f.color } });
    sB.addImage({ data: f.icon, x: fx + 0.22, y: fy + 0.25, w: 0.36, h: 0.36 });
    sB.addText(f.title, {
      x: fx + 0.8, y: fy + 0.05, w: 3.55, h: 0.32,
      fontSize: 12, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });
    sB.addText(f.desc, {
      x: fx + 0.8, y: fy + 0.38, w: 3.55, h: 0.46,
      fontSize: 9.5, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // ════════════════════════════════════════════
  // SLIDE C: SIGNAL QUALITY FIXES
  // ════════════════════════════════════════════
  let sC = pres.addSlide();
  sC.background = { color: C.navy };
  addSlideHeader(sC, pres, "Signal Quality Fixes");

  // 3 fix cards — large, prominent
  const fixes = [
    {
      icon: icons.chartW, color: "E74C3C", bgColor: "2A1020",
      badge: "BUG FIX 1",
      title: "Target Price for BUY Signals",
      problem: "Breakout stocks were showing target price below current price — indicating a sell when signal was BUY",
      fix: "Target is now always capped to current_price * 1.02 minimum for BUY signals, ensuring target > entry",
      impact: "No more contradictory signal/target pairs confusing trade decisions"
    },
    {
      icon: icons.warnW, color: "F39C12", bgColor: "201800",
      badge: "BUG FIX 2",
      title: "RS Ratio Formula Correction",
      problem: "Old formula: stock_return / nifty_return — inverted when NIFTY was negative, making weak stocks appear strong",
      fix: "Corrected to (1 + stock_return) / (1 + nifty_return) — handles negative benchmark correctly",
      impact: "Relative strength now accurately identifies outperformers vs the index in all market conditions"
    },
    {
      icon: icons.cogW, color: "3EC6E0", bgColor: "001820",
      badge: "BUG FIX 3",
      title: "Support / Resistance Selection",
      problem: "Silent None bug: when pivot levels were empty, nearest support/resistance returned None — causing downstream crash",
      fix: "Added None guard with fallback to current price ± ATR when no pivot levels are available",
      impact: "Stop-loss and target calculations now always return valid prices — no more silent failures"
    },
  ];

  fixes.forEach((fix, i) => {
    const fy = 0.88 + i * 1.5;

    sC.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: fy, w: 9.3, h: 1.35, fill: { color: fix.bgColor }, shadow: mkShadow() });
    // Left color bar
    sC.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: fy, w: 0.12, h: 1.35, fill: { color: fix.color } });

    // Badge
    sC.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: fy + 0.1, w: 1.0, h: 0.32, fill: { color: fix.color }, rectRadius: 0.06 });
    sC.addText(fix.badge, {
      x: 0.6, y: fy + 0.1, w: 1.0, h: 0.32,
      fontSize: 8, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });

    // Icon
    sC.addImage({ data: fix.icon, x: 0.62, y: fy + 0.55, w: 0.38, h: 0.38 });

    // Title
    sC.addText(fix.title, {
      x: 1.55, y: fy + 0.08, w: 7.85, h: 0.35,
      fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, margin: 0
    });

    // Problem / Fix in two columns
    sC.addText("Problem: ", {
      x: 1.55, y: fy + 0.46, w: 0.85, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: C.red, bold: true, margin: 0
    });
    sC.addText(fix.problem, {
      x: 2.4, y: fy + 0.46, w: 3.45, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: C.mutedText, margin: 0
    });

    sC.addText("Fix: ", {
      x: 1.55, y: fy + 0.78, w: 0.5, h: 0.28,
      fontSize: 10, fontFace: "Calibri", color: "2ECC71", bold: true, margin: 0
    });
    sC.addText(fix.fix, {
      x: 2.05, y: fy + 0.78, w: 3.8, h: 0.28,
      fontSize: 10, fontFace: "Calibri", color: C.mutedText, margin: 0
    });

    sC.addText("Impact: ", {
      x: 5.9, y: fy + 0.46, w: 0.72, h: 0.6,
      fontSize: 10, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0
    });
    sC.addText(fix.impact, {
      x: 6.62, y: fy + 0.46, w: 2.85, h: 0.6,
      fontSize: 9.5, fontFace: "Calibri", color: C.mutedText, margin: 0
    });
  });

  // Footer callout
  sC.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 5.1, w: 9.3, h: 0.4, fill: { color: C.deepNavy } });
  sC.addImage({ data: icons.check, x: 0.55, y: 5.16, w: 0.27, h: 0.27 });
  sC.addText("All 3 fixes ship in the same release — more accurate signals = better trade decisions", {
    x: 0.9, y: 5.1, w: 8.5, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.accentCyan, italic: true, valign: "middle", margin: 0
  });

  // ─── WRITE FILE ───
  const outputPath = "/Users/aryakirtisingh/intraday_trading/intraday_trading_presentation.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log("Saved to: " + outputPath);
}

createPresentation().catch(err => { console.error(err); process.exit(1); });
