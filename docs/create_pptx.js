const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// Icon imports
const {
  FaFileCode, FaCogs, FaExchangeAlt, FaShieldAlt, FaChartBar,
  FaCheckCircle, FaExclamationTriangle, FaRocket, FaQuestionCircle,
  FaLayerGroup, FaCodeBranch, FaUsers, FaSyncAlt, FaClipboardList,
  FaBug, FaLock, FaFlask, FaArrowRight, FaDatabase, FaCloud,
  FaTimes, FaSearch, FaWrench, FaBookOpen
} = require("react-icons/fa");

// ─── COLOR PALETTE (Midnight Executive) ───
const C = {
  navy:      "1E2761",
  deepNavy:  "141B3D",
  midBlue:   "2E4DA7",
  accentCyan:"3EC6E0",
  ice:       "CADCFC",
  lightBg:   "F0F4FC",
  white:     "FFFFFF",
  darkText:  "1A1A2E",
  mutedText: "5A6070",
  red:       "E74C3C",
  green:     "27AE60",
  amber:     "F39C12",
  cardBg:    "FFFFFF",
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

const mkShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });

async function createPresentation() {
  let pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Arya Kirti Singh";
  pres.title = "Parameterized Instruction Files for AI Agents";

  // Pre-render all icons
  const icons = {};
  const iconMap = {
    fileCode: [FaFileCode, "#" + C.accentCyan],
    cogs: [FaCogs, "#" + C.accentCyan],
    exchange: [FaExchangeAlt, "#" + C.white],
    shield: [FaShieldAlt, "#" + C.accentCyan],
    chart: [FaChartBar, "#" + C.accentCyan],
    check: [FaCheckCircle, "#" + C.green],
    warn: [FaExclamationTriangle, "#" + C.amber],
    rocket: [FaRocket, "#" + C.accentCyan],
    question: [FaQuestionCircle, "#" + C.white],
    layers: [FaLayerGroup, "#" + C.accentCyan],
    branch: [FaCodeBranch, "#" + C.accentCyan],
    users: [FaUsers, "#" + C.accentCyan],
    sync: [FaSyncAlt, "#" + C.accentCyan],
    clipboard: [FaClipboardList, "#" + C.accentCyan],
    bug: [FaBug, "#" + C.red],
    lock: [FaLock, "#" + C.accentCyan],
    flask: [FaFlask, "#" + C.accentCyan],
    arrow: [FaArrowRight, "#" + C.white],
    database: [FaDatabase, "#" + C.accentCyan],
    cloud: [FaCloud, "#" + C.accentCyan],
    times: [FaTimes, "#" + C.red],
    search: [FaSearch, "#" + C.accentCyan],
    wrench: [FaWrench, "#" + C.amber],
    book: [FaBookOpen, "#" + C.accentCyan],
    checkWhite: [FaCheckCircle, "#" + C.white],
    arrowCyan: [FaArrowRight, "#" + C.accentCyan],
    rocketWhite: [FaRocket, "#" + C.white],
    shieldWhite: [FaShieldAlt, "#" + C.white],
    timesWhite: [FaTimes, "#" + C.white],
    warnWhite: [FaExclamationTriangle, "#" + C.white],
    checkNavy: [FaCheckCircle, "#" + C.navy],
    bugWhite: [FaBug, "#" + C.white],
  };
  for (const [key, [Icon, color]] of Object.entries(iconMap)) {
    icons[key] = await iconToBase64Png(Icon, color);
  }

  // ═══════════════════════════════════════════
  // SLIDE 1: TITLE
  // ═══════════════════════════════════════════
  let s1 = pres.addSlide();
  s1.background = { color: C.deepNavy };
  // Decorative shape top-right
  s1.addShape(pres.shapes.RECTANGLE, { x: 6.5, y: -0.5, w: 4.5, h: 2.5, fill: { color: C.midBlue, transparency: 40 }, rotate: 15 });
  s1.addShape(pres.shapes.RECTANGLE, { x: 7.5, y: -1, w: 3.5, h: 2, fill: { color: C.accentCyan, transparency: 60 }, rotate: 20 });
  // Bottom accent bar
  s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.15, w: 10, h: 0.475, fill: { color: C.accentCyan } });

  s1.addImage({ data: icons.cogs, x: 0.7, y: 1.0, w: 0.6, h: 0.6 });
  s1.addText("Parameterized Instruction\nFiles for AI Agents", {
    x: 0.7, y: 1.7, w: 7.5, h: 1.6,
    fontSize: 34, fontFace: "Georgia", color: C.white, bold: true,
    lineSpacingMultiple: 1.1, margin: 0
  });
  s1.addText("Reducing Hallucination, Improving Maintainability & Enabling A/B Testing", {
    x: 0.7, y: 3.4, w: 7.5, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.ice, italic: true, margin: 0
  });
  s1.addText("Intraday Trading Assistant  |  Team Presentation", {
    x: 0.7, y: 4.2, w: 7.5, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.accentCyan, margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 2: AGENDA
  // ═══════════════════════════════════════════
  let s2 = pres.addSlide();
  s2.background = { color: C.lightBg };
  // Left accent strip
  s2.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.15, h: 5.625, fill: { color: C.navy } });

  s2.addText("Agenda", {
    x: 0.7, y: 0.3, w: 9, h: 0.7,
    fontSize: 32, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  const agendaItems = [
    "What are Parameterized Instructions?",
    "The Problem: Hardcoded Prompts in Our Project",
    "How Parameterized Instructions Work",
    "Template Structure & Example",
    "Before vs After: Our Codebase",
    "How This Reduces AI Hallucination",
    "Key Advantages",
    "Architecture Overview",
    "Implementation Plan (Phases)",
    "Risk & Mitigation",
    "Next Steps & Q&A"
  ];

  // Two columns for agenda
  const col1 = agendaItems.slice(0, 6);
  const col2 = agendaItems.slice(6);

  const agendaTextLeft = col1.map((item, i) => ({
    text: `${String(i + 1).padStart(2, "0")}   ${item}`,
    options: { breakLine: true, fontSize: 13, fontFace: "Calibri", color: C.darkText, paraSpaceAfter: 8 }
  }));
  s2.addText(agendaTextLeft, { x: 0.7, y: 1.2, w: 4.3, h: 3.8, margin: 0 });

  const agendaTextRight = col2.map((item, i) => ({
    text: `${String(i + 7).padStart(2, "0")}   ${item}`,
    options: { breakLine: true, fontSize: 13, fontFace: "Calibri", color: C.darkText, paraSpaceAfter: 8 }
  }));
  s2.addText(agendaTextRight, { x: 5.3, y: 1.2, w: 4.3, h: 3.8, margin: 0 });

  // Decorative circle
  s2.addShape(pres.shapes.OVAL, { x: 8.8, y: 4.3, w: 1.0, h: 1.0, fill: { color: C.accentCyan, transparency: 20 } });

  // ═══════════════════════════════════════════
  // SLIDE 3: WHAT ARE PARAMETERIZED INSTRUCTIONS?
  // ═══════════════════════════════════════════
  let s3 = pres.addSlide();
  s3.background = { color: C.white };
  s3.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s3.addText("What Are Parameterized Instruction Files?", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // Cards grid - 2x2 + analogy
  const cards3 = [
    { icon: icons.fileCode, title: "Standalone Templates", desc: "Prompts stored as YAML/JSON files,\nseparate from application code" },
    { icon: icons.cogs, title: "Runtime Variables", desc: "Placeholder {{variables}} filled\nwith actual data at execution time" },
    { icon: icons.layers, title: "Separation of Concerns", desc: "Isolate 'what to tell the AI'\nfrom 'how to call the AI'" },
    { icon: icons.branch, title: "Version Controlled", desc: "Testable, reviewable, and\ntrackable in git history" },
  ];

  cards3.forEach((card, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const cx = 0.7 + col * 4.5;
    const cy = 1.3 + row * 1.7;

    s3.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 4.0, h: 1.4, fill: { color: C.lightBg }, shadow: mkShadow() });
    s3.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 0.07, h: 1.4, fill: { color: C.accentCyan } });
    s3.addImage({ data: card.icon, x: cx + 0.25, y: cy + 0.25, w: 0.4, h: 0.4 });
    s3.addText(card.title, { x: cx + 0.8, y: cy + 0.15, w: 3.0, h: 0.35, fontSize: 14, fontFace: "Calibri", color: C.navy, bold: true, margin: 0 });
    s3.addText(card.desc, { x: cx + 0.8, y: cy + 0.55, w: 3.0, h: 0.7, fontSize: 11, fontFace: "Calibri", color: C.mutedText, margin: 0 });
  });

  // Analogy callout
  s3.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.7, w: 8.6, h: 0.65, fill: { color: C.navy } });
  s3.addImage({ data: icons.arrowCyan, x: 0.9, y: 4.82, w: 0.35, h: 0.35 });
  s3.addText("Think of it like Jinja2 templates for HTML — but for AI prompts", {
    x: 1.4, y: 4.7, w: 7.5, h: 0.65,
    fontSize: 13, fontFace: "Calibri", color: C.white, italic: true, valign: "middle", margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 4: THE PROBLEM
  // ═══════════════════════════════════════════
  let s4 = pres.addSlide();
  s4.background = { color: C.white };
  s4.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.red } });

  s4.addText("The Problem: Our Current State", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // 3 problem cards
  const problems = [
    { file: "bedrock.tf", desc: "TradingGuru agent instructions\n~2,400 chars buried in Terraform HCL", icon: icons.times },
    { file: "ai_validator.py", desc: "Signal validation prompt\ninline Python f-string", icon: icons.times },
    { file: "sentiment_agent.py", desc: "Nova Micro headline classifier\nhardcoded prompt string", icon: icons.times },
  ];

  problems.forEach((p, i) => {
    const cy = 1.2 + i * 1.2;
    s4.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: cy, w: 5.0, h: 0.85, fill: { color: "FEF0F0" }, shadow: mkShadow() });
    s4.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: cy, w: 0.07, h: 0.85, fill: { color: C.red } });
    s4.addImage({ data: p.icon, x: 0.95, y: cy + 0.2, w: 0.35, h: 0.35 });
    s4.addText(p.file, { x: 1.5, y: cy + 0.05, w: 3.8, h: 0.3, fontSize: 13, fontFace: "Consolas", color: C.red, bold: true, margin: 0 });
    s4.addText(p.desc, { x: 1.5, y: cy + 0.35, w: 3.8, h: 0.45, fontSize: 10.5, fontFace: "Calibri", color: C.mutedText, margin: 0 });
  });

  // Right side: consequences
  s4.addShape(pres.shapes.RECTANGLE, { x: 6.2, y: 1.2, w: 3.3, h: 3.6, fill: { color: C.lightBg }, shadow: mkShadow() });
  s4.addText("Consequences", { x: 6.4, y: 1.3, w: 3.0, h: 0.4, fontSize: 15, fontFace: "Georgia", color: C.navy, bold: true, margin: 0 });

  const consequences = [
    "Hard to review prompt changes in PRs",
    "No prompt versioning or history",
    "Cannot A/B test prompt variants",
    "Prompt logic mixed with business logic",
    "Easy to forget injecting required data",
    "Domain experts can't edit prompts"
  ];
  const consText = consequences.map(c => ({
    text: c,
    options: { bullet: true, breakLine: true, fontSize: 11, fontFace: "Calibri", color: C.mutedText, paraSpaceAfter: 6 }
  }));
  s4.addText(consText, { x: 6.4, y: 1.8, w: 2.9, h: 2.8, margin: 0 });

  // ═══════════════════════════════════════════
  // SLIDE 5: HOW IT WORKS (FLOW)
  // ═══════════════════════════════════════════
  let s5 = pres.addSlide();
  s5.background = { color: C.white };
  s5.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s5.addText("How Parameterized Instructions Work", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.7,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // Flow diagram: 4 boxes with arrows
  const flowSteps = [
    { label: "YAML\nTemplate", color: C.navy, icon: icons.fileCode },
    { label: "Prompt\nLoader", color: C.midBlue, icon: icons.cogs },
    { label: "Variables\nInjected", color: C.accentCyan, icon: icons.database },
    { label: "AI Model\nResponse", color: C.green, icon: icons.cloud },
  ];

  const flowY = 1.5;
  const boxW = 1.8;
  const gap = 0.45;
  const startX = (10 - (flowSteps.length * boxW + (flowSteps.length - 1) * gap)) / 2;

  flowSteps.forEach((step, i) => {
    const bx = startX + i * (boxW + gap);
    s5.addShape(pres.shapes.RECTANGLE, { x: bx, y: flowY, w: boxW, h: 1.5, fill: { color: step.color }, shadow: mkShadow() });
    s5.addImage({ data: step.icon, x: bx + (boxW - 0.4) / 2, y: flowY + 0.2, w: 0.4, h: 0.4 });
    s5.addText(step.label, {
      x: bx, y: flowY + 0.7, w: boxW, h: 0.7,
      fontSize: 12, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
    // Arrow between boxes
    if (i < flowSteps.length - 1) {
      s5.addImage({ data: icons.arrow, x: bx + boxW + 0.07, y: flowY + 0.5, w: 0.3, h: 0.3 });
    }
  });

  // Explanation below
  const explainItems = [
    { title: "Template File", desc: "YAML file with {{variable}} placeholders, model config, guardrails, and output schema" },
    { title: "Prompt Loader", desc: "Python module reads template, uses Jinja2 to render variables into final prompt string" },
    { title: "Runtime Injection", desc: "Actual stock data (RSI, MACD, price) fills placeholders at execution time" },
    { title: "AI Response", desc: "Model receives fully-formed prompt; response validated against output schema" },
  ];

  explainItems.forEach((item, i) => {
    const ey = 3.4 + Math.floor(i / 2) * 0.9;
    const ex = 0.7 + (i % 2) * 4.5;
    s5.addText(item.title, { x: ex, y: ey, w: 4.0, h: 0.3, fontSize: 12, fontFace: "Calibri", color: C.navy, bold: true, margin: 0 });
    s5.addText(item.desc, { x: ex, y: ey + 0.3, w: 4.0, h: 0.5, fontSize: 10.5, fontFace: "Calibri", color: C.mutedText, margin: 0 });
  });

  // ═══════════════════════════════════════════
  // SLIDE 6: TEMPLATE STRUCTURE
  // ═══════════════════════════════════════════
  let s6 = pres.addSlide();
  s6.background = { color: C.white };
  s6.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s6.addText("Template Structure: signal_validator.yaml", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 26, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // YAML code block (left)
  s6.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 5.2, h: 4.2, fill: { color: "1B1F2B" }, shadow: mkShadow() });
  const yamlLines = [
    { text: "name: signal_validator", options: { color: C.green, breakLine: true } },
    { text: "version: \"1.2\"", options: { color: C.green, breakLine: true } },
    { text: "model: claude-3-5-haiku", options: { color: C.ice, breakLine: true } },
    { text: "temperature: 0.2", options: { color: C.ice, breakLine: true } },
    { text: "max_tokens: 512", options: { color: C.ice, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "system: |", options: { color: C.amber, breakLine: true } },
    { text: "  You are a signal validation AI.", options: { color: C.white, breakLine: true } },
    { text: "  Never invent numbers.", options: { color: C.white, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "user_template: |", options: { color: C.amber, breakLine: true } },
    { text: "  Validate {{signal_direction}} for", options: { color: C.white, breakLine: true } },
    { text: "  {{symbol}}:", options: { color: C.white, breakLine: true } },
    { text: "  Price: {{current_price}}", options: { color: "3EC6E0", breakLine: true } },
    { text: "  RSI: {{rsi}} | MACD: {{macd}}", options: { color: "3EC6E0", breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "output_schema:", options: { color: C.amber, breakLine: true } },
    { text: "  required: [agrees, confidence,", options: { color: C.ice, breakLine: true } },
    { text: "    thesis, risk_flags]", options: { color: C.ice, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "guardrails:", options: { color: C.amber, breakLine: true } },
    { text: "  - Only reference provided data", options: { color: C.ice, breakLine: true } },
    { text: "  - Confidence must be 0.0-1.0", options: { color: C.ice } },
  ];
  s6.addText(yamlLines.map(l => ({
    text: l.text || " ",
    options: { ...l.options, fontSize: 10, fontFace: "Consolas" }
  })), { x: 0.7, y: 1.2, w: 4.8, h: 4.0, margin: 0, valign: "top" });

  // Right side: annotations
  const annotations = [
    { y: 1.2, label: "Metadata", desc: "Name + version for tracking" },
    { y: 1.8, label: "Model Config", desc: "Temperature & tokens alongside prompt" },
    { y: 2.7, label: "System Prompt", desc: "Base personality & constraints" },
    { y: 3.4, label: "User Template", desc: "{{variables}} filled at runtime" },
    { y: 4.1, label: "Output Schema", desc: "Validates AI response structure" },
    { y: 4.6, label: "Guardrails", desc: "Anti-hallucination constraints" },
  ];
  annotations.forEach(a => {
    s6.addShape(pres.shapes.RECTANGLE, { x: 6.0, y: a.y, w: 3.5, h: 0.45, fill: { color: C.lightBg } });
    s6.addShape(pres.shapes.RECTANGLE, { x: 6.0, y: a.y, w: 0.06, h: 0.45, fill: { color: C.accentCyan } });
    s6.addText(a.label, { x: 6.2, y: a.y, w: 3.2, h: 0.22, fontSize: 11, fontFace: "Calibri", color: C.navy, bold: true, margin: 0 });
    s6.addText(a.desc, { x: 6.2, y: a.y + 0.22, w: 3.2, h: 0.2, fontSize: 9.5, fontFace: "Calibri", color: C.mutedText, margin: 0 });
  });

  // ═══════════════════════════════════════════
  // SLIDE 7: BEFORE VS AFTER – SIGNAL VALIDATOR
  // ═══════════════════════════════════════════
  let s7 = pres.addSlide();
  s7.background = { color: C.white };
  s7.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s7.addText("Before vs After: Signal Validator", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 26, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // BEFORE (left)
  s7.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 4.3, h: 0.45, fill: { color: C.red } });
  s7.addText("BEFORE  —  ai_validator.py", { x: 0.7, y: 1.1, w: 4.0, h: 0.45, fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });

  s7.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.55, w: 4.3, h: 3.3, fill: { color: "1B1F2B" } });
  const beforeCode = [
    { text: "# Mixed in handler.py", options: { color: C.mutedText, breakLine: true } },
    { text: 'prompt = f"""You are a', options: { color: C.white, breakLine: true } },
    { text: '  signal validation AI.', options: { color: C.white, breakLine: true } },
    { text: '  The stock {symbol} has', options: { color: C.amber, breakLine: true } },
    { text: '  RSI={rsi}, MACD={macd},', options: { color: C.amber, breakLine: true } },
    { text: '  Volume={vol}...', options: { color: C.amber, breakLine: true } },
    { text: '  Never invent numbers.', options: { color: C.white, breakLine: true } },
    { text: '  Return JSON with agrees,', options: { color: C.white, breakLine: true } },
    { text: '  confidence, thesis..."""', options: { color: C.white, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "response = bedrock.invoke(", options: { color: C.ice, breakLine: true } },
    { text: "  model=HAIKU_ID,", options: { color: C.ice, breakLine: true } },
    { text: "  body={prompt, temp=0.2}", options: { color: C.ice, breakLine: true } },
    { text: ")", options: { color: C.ice } },
  ];
  s7.addText(beforeCode.map(l => ({ text: l.text || " ", options: { ...l.options, fontSize: 9, fontFace: "Consolas" } })),
    { x: 0.7, y: 1.65, w: 3.9, h: 3.1, margin: 0, valign: "top" });

  // AFTER (right)
  s7.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.1, w: 4.3, h: 0.45, fill: { color: C.green } });
  s7.addText("AFTER  —  Clean Separation", { x: 5.4, y: 1.1, w: 4.0, h: 0.45, fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });

  s7.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.55, w: 4.3, h: 3.3, fill: { color: "1B1F2B" } });
  const afterCode = [
    { text: "# handler.py (3 lines)", options: { color: C.mutedText, breakLine: true } },
    { text: "from prompt_loader import", options: { color: C.ice, breakLine: true } },
    { text: "  load_prompt", options: { color: C.ice, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: 'cfg = load_prompt(', options: { color: C.green, breakLine: true } },
    { text: '  "signal_validator",', options: { color: C.green, breakLine: true } },
    { text: '  {"symbol": sym,', options: { color: C.amber, breakLine: true } },
    { text: '   "rsi": rsi,', options: { color: C.amber, breakLine: true } },
    { text: '   "macd": macd, ...}', options: { color: C.amber, breakLine: true } },
    { text: ")", options: { color: C.green, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "# Prompt lives in YAML", options: { color: C.mutedText, breakLine: true } },
    { text: "# Model config in YAML", options: { color: C.mutedText, breakLine: true } },
    { text: "# Schema in YAML", options: { color: C.mutedText } },
  ];
  s7.addText(afterCode.map(l => ({ text: l.text || " ", options: { ...l.options, fontSize: 9, fontFace: "Consolas" } })),
    { x: 5.4, y: 1.65, w: 3.9, h: 3.1, margin: 0, valign: "top" });

  // Bottom callout
  s7.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.0, w: 9.0, h: 0.45, fill: { color: C.lightBg } });
  s7.addImage({ data: icons.check, x: 0.65, y: 5.05, w: 0.3, h: 0.3 });
  s7.addText("Prompt is now reviewable, versionable, and testable independently of application code", {
    x: 1.1, y: 5.0, w: 8.2, h: 0.45, fontSize: 12, fontFace: "Calibri", color: C.navy, valign: "middle", margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 8: BEFORE VS AFTER – BEDROCK AGENT
  // ═══════════════════════════════════════════
  let s8 = pres.addSlide();
  s8.background = { color: C.white };
  s8.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s8.addText("Before vs After: TradingGuru Agent", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 26, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // Before card
  s8.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 4.3, h: 2.8, fill: { color: "FEF0F0" }, shadow: mkShadow() });
  s8.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 4.3, h: 0.45, fill: { color: C.red } });
  s8.addText("BEFORE", { x: 0.7, y: 1.1, w: 2, h: 0.45, fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });

  const beforeItems8 = [
    "~2,400 chars inline in bedrock.tf",
    "Prompt changes buried in Terraform diffs",
    "Only Terraform-savvy devs can edit",
    "No way to A/B test prompt variants",
    "Prompt + infra changes in same PR",
  ];
  s8.addText(beforeItems8.map(t => ({ text: t, options: { bullet: true, breakLine: true, fontSize: 11, fontFace: "Calibri", color: C.darkText, paraSpaceAfter: 6 } })),
    { x: 0.7, y: 1.7, w: 3.9, h: 2.0, margin: 0 });

  // After card
  s8.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.1, w: 4.3, h: 2.8, fill: { color: "F0FEF0" }, shadow: mkShadow() });
  s8.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.1, w: 4.3, h: 0.45, fill: { color: C.green } });
  s8.addText("AFTER", { x: 5.4, y: 1.1, w: 2, h: 0.45, fontSize: 14, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });

  const afterItems8 = [
    "Standalone trading_guru_agent.yaml",
    "Clean, reviewable prompt-only PRs",
    "Traders can edit YAML directly",
    "Swap v1 vs v2 via config flag",
    "Terraform reads file via templatefile()",
  ];
  s8.addText(afterItems8.map(t => ({ text: t, options: { bullet: true, breakLine: true, fontSize: 11, fontFace: "Calibri", color: C.darkText, paraSpaceAfter: 6 } })),
    { x: 5.4, y: 1.7, w: 3.9, h: 2.0, margin: 0 });

  // Bottom highlight
  s8.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.2, w: 9.0, h: 1.1, fill: { color: C.navy } });
  s8.addImage({ data: icons.rocketWhite, x: 0.75, y: 4.4, w: 0.4, h: 0.4 });
  s8.addText("Key Insight", { x: 1.3, y: 4.3, w: 3, h: 0.35, fontSize: 14, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0 });
  s8.addText("Domain experts (traders) can now iterate on prompt quality without\ntouching infrastructure code — reducing deployment friction by 80%", {
    x: 1.3, y: 4.65, w: 7.8, h: 0.55, fontSize: 12, fontFace: "Calibri", color: C.white, margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 9: REDUCING HALLUCINATION
  // ═══════════════════════════════════════════
  let s9 = pres.addSlide();
  s9.background = { color: C.white };
  s9.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s9.addText("How This Reduces AI Hallucination", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 26, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  const hallucinationCards = [
    {
      num: "01", title: "Structured Grounding",
      desc: "Explicit {{variable}} slots ensure all required data is injected. Structurally impossible to forget passing RSI, MACD, or price data.",
      color: C.midBlue,
    },
    {
      num: "02", title: "Output Schema Enforcement",
      desc: "Validate AI response against declared schema. Catch hallucinated or missing fields immediately before they reach users.",
      color: C.accentCyan,
    },
    {
      num: "03", title: "Guardrails Section",
      desc: "System-level constraints injected consistently: 'only reference provided data', 'say INSUFFICIENT_DATA if missing'.",
      color: C.navy,
    },
    {
      num: "04", title: "Measurable A/B Testing",
      desc: "Version prompts (v1.2 vs v1.3), compare contradiction rates and confidence scores. Iterate with data, not guesswork.",
      color: C.green,
    },
  ];

  hallucinationCards.forEach((card, i) => {
    const cy = 1.1 + i * 0.95;
    s9.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: cy, w: 8.6, h: 0.82, fill: { color: C.lightBg }, shadow: mkShadow() });
    // Number circle
    s9.addShape(pres.shapes.OVAL, { x: 0.9, y: cy + 0.13, w: 0.5, h: 0.5, fill: { color: card.color } });
    s9.addText(card.num, { x: 0.9, y: cy + 0.13, w: 0.5, h: 0.5, fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
    s9.addText(card.title, { x: 1.65, y: cy + 0.06, w: 7.3, h: 0.28, fontSize: 13, fontFace: "Calibri", color: C.navy, bold: true, margin: 0 });
    s9.addText(card.desc, { x: 1.65, y: cy + 0.36, w: 7.3, h: 0.38, fontSize: 10, fontFace: "Calibri", color: C.mutedText, margin: 0 });
  });

  // Bottom stat
  s9.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 5.0, w: 8.6, h: 0.45, fill: { color: C.navy } });
  s9.addText("Result: Every prompt invocation is grounded, validated, and measurable", {
    x: 0.7, y: 5.0, w: 8.6, h: 0.45, fontSize: 12, fontFace: "Calibri", color: C.accentCyan, bold: true, align: "center", valign: "middle", margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 10: KEY ADVANTAGES
  // ═══════════════════════════════════════════
  let s10 = pres.addSlide();
  s10.background = { color: C.white };
  s10.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s10.addText("Key Advantages", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  const advantages = [
    { icon: icons.branch, title: "Version Control", desc: "Clean prompt diffs in git, not buried in code" },
    { icon: icons.flask, title: "A/B Testing", desc: "Swap prompt versions without redeploying" },
    { icon: icons.layers, title: "Separation of Concerns", desc: "Prompt logic isolated from business logic" },
    { icon: icons.sync, title: "Reusability", desc: "Shared partials across multiple prompts" },
    { icon: icons.shield, title: "Schema Validation", desc: "Catch bad AI responses before users see them" },
    { icon: icons.users, title: "Non-Dev Editing", desc: "Domain experts can tweak YAML directly" },
  ];

  advantages.forEach((adv, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const cx = 0.5 + col * 3.1;
    const cy = 1.15 + row * 2.0;

    s10.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 2.85, h: 1.7, fill: { color: C.lightBg }, shadow: mkShadow() });
    s10.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 2.85, h: 0.06, fill: { color: C.accentCyan } });
    s10.addImage({ data: adv.icon, x: cx + 0.15, y: cy + 0.25, w: 0.4, h: 0.4 });
    s10.addText(adv.title, { x: cx + 0.7, y: cy + 0.25, w: 2.0, h: 0.35, fontSize: 13, fontFace: "Calibri", color: C.navy, bold: true, margin: 0 });
    s10.addText(adv.desc, { x: cx + 0.15, y: cy + 0.8, w: 2.55, h: 0.7, fontSize: 11, fontFace: "Calibri", color: C.mutedText, margin: 0 });
  });

  // ═══════════════════════════════════════════
  // SLIDE 11: ARCHITECTURE OVERVIEW
  // ═══════════════════════════════════════════
  let s11 = pres.addSlide();
  s11.background = { color: C.white };
  s11.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s11.addText("Architecture Overview", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  // Directory structure (left)
  s11.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 4.3, h: 3.8, fill: { color: "1B1F2B" }, shadow: mkShadow() });
  s11.addText("Directory Structure", { x: 0.7, y: 1.15, w: 3.5, h: 0.35, fontSize: 12, fontFace: "Calibri", color: C.accentCyan, bold: true, margin: 0 });

  const dirLines = [
    { text: "intraday_trading/", options: { color: C.white, bold: true, breakLine: true } },
    { text: "  prompts/", options: { color: C.amber, bold: true, breakLine: true } },
    { text: "    signal_validator.yaml", options: { color: C.ice, breakLine: true } },
    { text: "    headline_classifier.yaml", options: { color: C.ice, breakLine: true } },
    { text: "    trading_guru_agent.yaml", options: { color: C.ice, breakLine: true } },
    { text: "    _partials/", options: { color: C.amber, breakLine: true } },
    { text: "      stock_context.yaml", options: { color: C.ice, breakLine: true } },
    { text: "  backend/", options: { color: C.amber, bold: true, breakLine: true } },
    { text: "    prompt_loader.py", options: { color: "3EC6E0", bold: true, breakLine: true } },
    { text: "  lambdas/", options: { color: C.amber, bold: true, breakLine: true } },
    { text: "    shared/  (Lambda Layer)", options: { color: C.ice, breakLine: true } },
    { text: "      prompt_loader.py", options: { color: "3EC6E0", breakLine: true } },
    { text: "      prompts/  (bundled)", options: { color: "3EC6E0" } },
  ];
  s11.addText(dirLines.map(l => ({ text: l.text, options: { ...l.options, fontSize: 10, fontFace: "Consolas" } })),
    { x: 0.7, y: 1.55, w: 3.9, h: 3.2, margin: 0, valign: "top" });

  // Flow diagram (right)
  s11.addText("Runtime Flow", { x: 5.3, y: 1.1, w: 4.0, h: 0.35, fontSize: 14, fontFace: "Georgia", color: C.navy, bold: true, margin: 0 });

  const flowBoxes = [
    { label: "Lambda Handler", color: C.midBlue, y: 1.6 },
    { label: "prompt_loader.py", color: C.accentCyan, y: 2.45 },
    { label: "prompts/*.yaml", color: C.amber, y: 3.3 },
    { label: "Bedrock API", color: C.navy, y: 4.15 },
  ];

  flowBoxes.forEach((box, i) => {
    s11.addShape(pres.shapes.RECTANGLE, { x: 5.5, y: box.y, w: 3.5, h: 0.6, fill: { color: box.color }, shadow: mkShadow() });
    s11.addText(box.label, { x: 5.5, y: box.y, w: 3.5, h: 0.6, fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
    if (i < flowBoxes.length - 1) {
      // Down arrow
      s11.addText("\u2193", { x: 6.9, y: box.y + 0.55, w: 0.7, h: 0.35, fontSize: 20, fontFace: "Calibri", color: C.mutedText, align: "center", margin: 0 });
    }
  });

  // ═══════════════════════════════════════════
  // SLIDE 12: IMPLEMENTATION PLAN
  // ═══════════════════════════════════════════
  let s12 = pres.addSlide();
  s12.background = { color: C.white };
  s12.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s12.addText("Implementation Plan", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  const phases = [
    { num: "1", title: "Prompt Directory + Loader", desc: "Create prompts/ dir & prompt_loader.py (~50 lines)", effort: "Day 1" },
    { num: "2", title: "Migrate Signal Validator", desc: "Easiest — self-contained in one Lambda", effort: "Day 1" },
    { num: "3", title: "Migrate Headline Classifier", desc: "Small prompt in sentiment_agent.py, quick win", effort: "Day 2" },
    { num: "4", title: "Migrate TradingGuru Agent", desc: "Biggest impact — Terraform templatefile() integration", effort: "Day 2-3" },
    { num: "5", title: "Add Schema Validation", desc: "Output validation + guardrails enforcement", effort: "Day 3" },
    { num: "6", title: "Lambda Layer Integration", desc: "Bundle into shared layer for all Lambdas", effort: "Day 4" },
  ];

  phases.forEach((phase, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const cx = 0.5 + col * 4.7;
    const cy = 1.15 + row * 1.35;

    s12.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 4.4, h: 1.15, fill: { color: C.lightBg }, shadow: mkShadow() });
    // Phase number
    s12.addShape(pres.shapes.OVAL, { x: cx + 0.15, y: cy + 0.3, w: 0.5, h: 0.5, fill: { color: C.navy } });
    s12.addText(phase.num, { x: cx + 0.15, y: cy + 0.3, w: 0.5, h: 0.5, fontSize: 16, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
    s12.addText(phase.title, { x: cx + 0.8, y: cy + 0.12, w: 3.0, h: 0.3, fontSize: 13, fontFace: "Calibri", color: C.navy, bold: true, margin: 0 });
    s12.addText(phase.desc, { x: cx + 0.8, y: cy + 0.42, w: 3.0, h: 0.35, fontSize: 10.5, fontFace: "Calibri", color: C.mutedText, margin: 0 });
    // Effort badge
    s12.addShape(pres.shapes.RECTANGLE, { x: cx + 3.4, y: cy + 0.15, w: 0.85, h: 0.3, fill: { color: C.accentCyan } });
    s12.addText(phase.effort, { x: cx + 3.4, y: cy + 0.15, w: 0.85, h: 0.3, fontSize: 9, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
  });

  // Bottom bar
  s12.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.0, w: 9.0, h: 0.45, fill: { color: C.navy } });
  s12.addText("Total estimated effort: 4 working days  |  Zero downtime migration", {
    x: 0.5, y: 5.0, w: 9.0, h: 0.45, fontSize: 12, fontFace: "Calibri", color: C.accentCyan, bold: true, align: "center", valign: "middle", margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 13: RISK & MITIGATION
  // ═══════════════════════════════════════════
  let s13 = pres.addSlide();
  s13.background = { color: C.white };
  s13.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.amber } });

  s13.addText("Risk & Mitigation", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  const risks = [
    { risk: "Extra file I/O at runtime", mitigation: "Cache loaded templates in memory — files are tiny (<5KB)", severity: "Low" },
    { risk: "Jinja2 dependency added", mitigation: "Lightweight, already common in Python ecosystem, no security risk", severity: "Low" },
    { risk: "Template syntax errors", mitigation: "Add CI validation step: lint YAML + render with test variables", severity: "Med" },
    { risk: "Breaking existing prompts", mitigation: "Migrate one at a time, compare outputs before/after for 100 stocks", severity: "Med" },
  ];

  // Table header
  s13.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.15, w: 9.0, h: 0.5, fill: { color: C.navy } });
  s13.addText("Risk", { x: 0.7, y: 1.15, w: 2.5, h: 0.5, fontSize: 12, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });
  s13.addText("Mitigation", { x: 3.4, y: 1.15, w: 4.8, h: 0.5, fontSize: 12, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", margin: 0 });
  s13.addText("Severity", { x: 8.4, y: 1.15, w: 1.0, h: 0.5, fontSize: 12, fontFace: "Calibri", color: C.white, bold: true, valign: "middle", align: "center", margin: 0 });

  risks.forEach((r, i) => {
    const ry = 1.75 + i * 0.85;
    const bgColor = i % 2 === 0 ? C.lightBg : C.white;
    s13.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: ry, w: 9.0, h: 0.75, fill: { color: bgColor } });
    s13.addText(r.risk, { x: 0.7, y: ry, w: 2.5, h: 0.75, fontSize: 11, fontFace: "Calibri", color: C.darkText, bold: true, valign: "middle", margin: 0 });
    s13.addText(r.mitigation, { x: 3.4, y: ry, w: 4.8, h: 0.75, fontSize: 11, fontFace: "Calibri", color: C.mutedText, valign: "middle", margin: 0 });
    const sevColor = r.severity === "Low" ? C.green : C.amber;
    s13.addShape(pres.shapes.RECTANGLE, { x: 8.55, y: ry + 0.2, w: 0.8, h: 0.3, fill: { color: sevColor } });
    s13.addText(r.severity, { x: 8.55, y: ry + 0.2, w: 0.8, h: 0.3, fontSize: 10, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0 });
  });

  // ═══════════════════════════════════════════
  // SLIDE 14: NEXT STEPS
  // ═══════════════════════════════════════════
  let s14 = pres.addSlide();
  s14.background = { color: C.white };
  s14.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accentCyan } });

  s14.addText("Next Steps", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6,
    fontSize: 28, fontFace: "Georgia", color: C.navy, bold: true, margin: 0
  });

  const nextSteps = [
    { icon: icons.checkNavy, text: "Approve the parameterized instructions approach" },
    { icon: icons.flask, text: "Build signal_validator.yaml as proof of concept" },
    { icon: icons.chart, text: "Measure signal accuracy before vs after migration" },
    { icon: icons.rocket, text: "Roll out to headline classifier and TradingGuru agent" },
    { icon: icons.wrench, text: "Add CI/CD validation for prompt template files" },
  ];

  nextSteps.forEach((step, i) => {
    const sy = 1.2 + i * 0.8;
    s14.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: sy, w: 7.0, h: 0.6, fill: { color: C.lightBg }, shadow: mkShadow() });
    s14.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: sy, w: 0.06, h: 0.6, fill: { color: C.accentCyan } });
    s14.addImage({ data: step.icon, x: 1.75, y: sy + 0.12, w: 0.35, h: 0.35 });
    s14.addText(step.text, { x: 2.3, y: sy, w: 5.8, h: 0.6, fontSize: 14, fontFace: "Calibri", color: C.darkText, valign: "middle", margin: 0 });
  });

  // Timeline hint
  s14.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 5.0, w: 7.0, h: 0.4, fill: { color: C.navy } });
  s14.addText("Target: Full migration complete within 1 sprint", {
    x: 1.5, y: 5.0, w: 7.0, h: 0.4, fontSize: 12, fontFace: "Calibri", color: C.accentCyan, bold: true, align: "center", valign: "middle", margin: 0
  });

  // ═══════════════════════════════════════════
  // SLIDE 15: Q&A
  // ═══════════════════════════════════════════
  let s15 = pres.addSlide();
  s15.background = { color: C.deepNavy };
  // Decorative shapes
  s15.addShape(pres.shapes.RECTANGLE, { x: -1, y: 3.5, w: 4, h: 3, fill: { color: C.midBlue, transparency: 40 }, rotate: -10 });
  s15.addShape(pres.shapes.OVAL, { x: 7.5, y: 0.5, w: 3, h: 3, fill: { color: C.accentCyan, transparency: 70 } });
  // Bottom accent bar
  s15.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.15, w: 10, h: 0.475, fill: { color: C.accentCyan } });

  s15.addImage({ data: icons.question, x: 4.3, y: 1.0, w: 1.0, h: 1.0 });
  s15.addText("Questions & Discussion", {
    x: 1, y: 2.2, w: 8, h: 0.8,
    fontSize: 36, fontFace: "Georgia", color: C.white, bold: true, align: "center", margin: 0
  });
  s15.addText("Let's shape the best approach for our trading platform together", {
    x: 1, y: 3.1, w: 8, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.ice, italic: true, align: "center", margin: 0
  });
  s15.addText("Intraday Trading Assistant  |  AI Agent Architecture", {
    x: 1, y: 3.8, w: 8, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.accentCyan, align: "center", margin: 0
  });

  // ─── WRITE FILE ───
  const outputPath = "/Users/aryakirtisingh/intraday_trading/docs/parameterized_instructions_presentation.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log("Presentation saved to: " + outputPath);
}

createPresentation().catch(err => { console.error(err); process.exit(1); });
