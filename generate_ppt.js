const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33" x 7.5"
pres.author = "Arya Singh";
pres.title = "AWS DevOps — CodePipeline, CodeBuild, CodeDeploy";

// ─────────────────────────────────────────────────────────────
// Color palette — AWS-inspired dark professional
// ─────────────────────────────────────────────────────────────
const C = {
  navy:    "232F3E",  // AWS dark navy
  orange:  "FF9900",  // AWS orange accent
  blue:    "146EB4",  // AWS blue secondary
  lightBg: "F7F8FA",  // subtle page background
  cardBg:  "FFFFFF",
  textDk:  "232F3E",
  textMd:  "4A5568",
  textLt:  "8A96A3",
  divider: "E2E8F0",
  success: "2D9B69",
  danger:  "D64545",
};

const FONT_H = "Calibri";
const FONT_B = "Calibri";

// Helpers for consistent styling
const mkShadow = () => ({ type: "outer", blur: 8, offset: 2, angle: 90, color: "000000", opacity: 0.08 });

// Footer bar
function addFooter(slide, pageNum) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 7.2, w: 13.33, h: 0.3, fill: { color: C.navy }, line: { color: C.navy }
  });
  slide.addText("AWS DevOps  |  Intraday Trading Platform", {
    x: 0.5, y: 7.2, w: 8, h: 0.3, fontSize: 10, color: "CADCFC", fontFace: FONT_B, valign: "middle", margin: 0
  });
  slide.addText(`${pageNum}`, {
    x: 12.5, y: 7.2, w: 0.5, h: 0.3, fontSize: 10, color: C.orange, fontFace: FONT_B, align: "right", valign: "middle", bold: true, margin: 0
  });
}

// ═════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ═════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Decorative orange accent bar on left
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.3, h: 7.5, fill: { color: C.orange }, line: { color: C.orange }
  });

  // Eyebrow label
  s.addText("TECH TALK  /  APR 2026", {
    x: 1.0, y: 1.8, w: 11, h: 0.4, fontSize: 14, color: C.orange,
    fontFace: FONT_B, bold: true, charSpacing: 6, margin: 0
  });

  // Main title
  s.addText("AWS DevOps in Action", {
    x: 1.0, y: 2.3, w: 11, h: 1.2, fontSize: 54, color: "FFFFFF",
    fontFace: FONT_H, bold: true, margin: 0
  });

  // Subtitle
  s.addText("Building a production-grade CI/CD pipeline with CodePipeline, CodeBuild, and CodeDeploy", {
    x: 1.0, y: 3.5, w: 11, h: 0.8, fontSize: 20, color: "CADCFC",
    fontFace: FONT_B, italic: true, margin: 0
  });

  // Divider line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.0, y: 4.8, w: 1.5, h: 0.04, fill: { color: C.orange }, line: { color: C.orange }
  });

  // Presenter
  s.addText([
    { text: "Presented by ", options: { color: "8A96A3", fontSize: 14 } },
    { text: "Arya Singh", options: { color: "FFFFFF", fontSize: 14, bold: true } },
  ], { x: 1.0, y: 5.0, w: 11, h: 0.4, fontFace: FONT_B, margin: 0 });

  s.addText("Case study: intraday_trading — a serverless trading analytics platform", {
    x: 1.0, y: 5.4, w: 11, h: 0.4, fontSize: 13, color: C.textLt, fontFace: FONT_B, margin: 0
  });
}

// ═════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM + SERVICES OVERVIEW
// ═════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  // Title
  s.addText("Why DevOps? The Three Pillars", {
    x: 0.5, y: 0.4, w: 12.3, h: 0.6, fontSize: 32, color: C.navy,
    fontFace: FONT_H, bold: true, margin: 0
  });
  s.addText("Automate the path from code → production, safely and repeatably.", {
    x: 0.5, y: 1.0, w: 12.3, h: 0.4, fontSize: 16, color: C.textMd,
    fontFace: FONT_B, italic: true, margin: 0
  });

  // The problem box
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.7, w: 12.3, h: 0.8,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addText([
    { text: "THE PROBLEM:  ", options: { color: C.orange, bold: true, fontSize: 13 } },
    { text: "Without automation, every deploy means manual terraform apply, manual S3 sync, manual CloudFront invalidation — slow, error-prone, no safety net, and no audit trail.",
      options: { color: "FFFFFF", fontSize: 13 } }
  ], { x: 0.8, y: 1.7, w: 11.8, h: 0.8, fontFace: FONT_B, valign: "middle", margin: 0 });

  // Three service cards
  const cards = [
    {
      x: 0.5, name: "CodePipeline", tagline: "The Orchestrator",
      desc: "Connects GitHub → Build → Deploy. Defines stages, gates, and artifact flow. The conductor of the symphony.",
      role: "WHAT FIRES WHEN"
    },
    {
      x: 4.77, name: "CodeBuild", tagline: "The Worker",
      desc: "Runs commands in ephemeral Linux containers — compiles, tests, plans Terraform, publishes artifacts. The muscle.",
      role: "RUNS YOUR CODE"
    },
    {
      x: 9.05, name: "CodeDeploy", tagline: "The Safe Lander",
      desc: "Shifts Lambda traffic gradually, watches CloudWatch alarms, auto-rollbacks on errors. The parachute.",
      role: "DELIVERS SAFELY"
    }
  ];

  cards.forEach(c => {
    // Card bg
    s.addShape(pres.shapes.RECTANGLE, {
      x: c.x, y: 2.8, w: 3.78, h: 4.0,
      fill: { color: C.cardBg }, line: { color: C.divider, width: 1 },
      shadow: mkShadow()
    });
    // Orange top bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: c.x, y: 2.8, w: 3.78, h: 0.12,
      fill: { color: C.orange }, line: { color: C.orange }
    });
    // Role label
    s.addText(c.role, {
      x: c.x + 0.3, y: 3.0, w: 3.3, h: 0.3, fontSize: 10,
      color: C.orange, bold: true, charSpacing: 4, fontFace: FONT_B, margin: 0
    });
    // Service name
    s.addText(c.name, {
      x: c.x + 0.3, y: 3.35, w: 3.3, h: 0.6, fontSize: 26,
      color: C.navy, bold: true, fontFace: FONT_H, margin: 0
    });
    // Tagline
    s.addText(c.tagline, {
      x: c.x + 0.3, y: 3.95, w: 3.3, h: 0.4, fontSize: 15,
      color: C.blue, italic: true, fontFace: FONT_B, margin: 0
    });
    // Divider
    s.addShape(pres.shapes.RECTANGLE, {
      x: c.x + 0.3, y: 4.45, w: 0.6, h: 0.03,
      fill: { color: C.orange }, line: { color: C.orange }
    });
    // Description
    s.addText(c.desc, {
      x: c.x + 0.3, y: 4.65, w: 3.3, h: 2.0, fontSize: 13,
      color: C.textMd, fontFace: FONT_B, valign: "top", margin: 0
    });
  });

  addFooter(s, 2);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 3 — ARCHITECTURE / TWO-PIPELINE DESIGN
// ═════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  // Title
  s.addText("Two Pipelines, One Repo", {
    x: 0.5, y: 0.4, w: 12.3, h: 0.6, fontSize: 32, color: C.navy,
    fontFace: FONT_H, bold: true, margin: 0
  });
  s.addText("Path-based routing: infra and frontend changes have different risk profiles — they deserve different pipelines.", {
    x: 0.5, y: 1.0, w: 12.3, h: 0.4, fontSize: 15, color: C.textMd,
    fontFace: FONT_B, italic: true, margin: 0
  });

  // GitHub source node (top center)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.4, y: 1.7, w: 2.5, h: 0.7, rectRadius: 0.08,
    fill: { color: C.navy }, line: { color: C.navy }, shadow: mkShadow()
  });
  s.addText("GitHub — main branch", {
    x: 5.4, y: 1.7, w: 2.5, h: 0.7, fontSize: 14, color: "FFFFFF",
    bold: true, align: "center", valign: "middle", fontFace: FONT_B, margin: 0
  });

  // Decision diamond - CodeStar connection
  s.addText("▼  CodeStar Connection  ▼", {
    x: 5.4, y: 2.45, w: 2.5, h: 0.3, fontSize: 11, color: C.orange,
    bold: true, align: "center", valign: "middle", fontFace: FONT_B, margin: 0
  });

  // Branch lines — visual paths
  s.addShape(pres.shapes.LINE, {
    x: 6.65, y: 2.75, w: -3.5, h: 0.45, line: { color: C.textLt, width: 2 }
  });
  s.addShape(pres.shapes.LINE, {
    x: 6.65, y: 2.75, w: 3.5, h: 0.45, line: { color: C.textLt, width: 2 }
  });

  // LEFT — Infra pipeline card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.2, w: 6.15, h: 3.7,
    fill: { color: C.cardBg }, line: { color: C.divider, width: 1 },
    shadow: mkShadow()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.2, w: 0.1, h: 3.7,
    fill: { color: C.orange }, line: { color: C.orange }
  });
  s.addText("trading-infra-pipeline", {
    x: 0.8, y: 3.3, w: 5.7, h: 0.5, fontSize: 20, color: C.navy,
    bold: true, fontFace: FONT_H, margin: 0
  });
  s.addText("Triggers on: infrastructure/**, lambdas/**, backend/**, prompts/**", {
    x: 0.8, y: 3.78, w: 5.7, h: 0.35, fontSize: 11, color: C.textMd,
    italic: true, fontFace: FONT_B, margin: 0
  });

  const infraStages = [
    { name: "Source",           desc: "— pull from GitHub", color: C.navy },
    { name: "BuildLayers",      desc: "— cross-compile Python deps", color: C.navy },
    { name: "TerraformPlan",    desc: "— diff against AWS state", color: C.navy },
    { name: "Manual Approval",  desc: "— SNS email gate", color: C.danger },
    { name: "TerraformApply",   desc: "— apply + CodeDeploy", color: C.navy },
  ];
  infraStages.forEach((st, i) => {
    const y = 4.2 + i * 0.48;
    s.addShape(pres.shapes.OVAL, {
      x: 0.95, y: y + 0.12, w: 0.12, h: 0.12,
      fill: { color: C.orange }, line: { color: C.orange }
    });
    s.addText([
      { text: st.name + "  ", options: { bold: true, color: st.color } },
      { text: st.desc, options: { color: C.textMd } },
    ], { x: 1.2, y: y, w: 5.3, h: 0.4, fontSize: 13, fontFace: FONT_B, valign: "middle", margin: 0 });
  });

  // RIGHT — Frontend pipeline card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 3.2, w: 6.0, h: 3.7,
    fill: { color: C.cardBg }, line: { color: C.divider, width: 1 },
    shadow: mkShadow()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 3.2, w: 0.1, h: 3.7,
    fill: { color: C.blue }, line: { color: C.blue }
  });
  s.addText("trading-frontend-pipeline", {
    x: 7.15, y: 3.3, w: 5.5, h: 0.5, fontSize: 20, color: C.navy,
    bold: true, fontFace: FONT_H, margin: 0
  });
  s.addText("Triggers on: frontend/**", {
    x: 7.15, y: 3.78, w: 5.5, h: 0.35, fontSize: 11, color: C.textMd,
    italic: true, fontFace: FONT_B, margin: 0
  });

  const frontStages = [
    { name: "Source",  desc: "— pull from GitHub" },
    { name: "Deploy",  desc: "— sync to S3" },
  ];
  frontStages.forEach((st, i) => {
    const y = 4.2 + i * 0.48;
    s.addShape(pres.shapes.OVAL, {
      x: 7.3, y: y + 0.12, w: 0.12, h: 0.12,
      fill: { color: C.blue }, line: { color: C.blue }
    });
    s.addText([
      { text: st.name + "  ", options: { bold: true, color: C.navy } },
      { text: st.desc, options: { color: C.textMd } },
    ], { x: 7.55, y: y, w: 5.15, h: 0.4, fontSize: 13, fontFace: FONT_B, valign: "middle", margin: 0 });
  });
  s.addText("└ Cache-control headers by file type", {
    x: 7.55, y: 5.2, w: 5.15, h: 0.3, fontSize: 11, color: C.textLt, fontFace: FONT_B, margin: 0
  });
  s.addText("└ CloudFront invalidation", {
    x: 7.55, y: 5.5, w: 5.15, h: 0.3, fontSize: 11, color: C.textLt, fontFace: FONT_B, margin: 0
  });
  s.addText("Fast path — no approval gate needed", {
    x: 7.15, y: 6.25, w: 5.5, h: 0.4, fontSize: 13, color: C.success,
    italic: true, bold: true, fontFace: FONT_B, margin: 0
  });

  addFooter(s, 3);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 4 — CODEBUILD STAGES (INFRA PIPELINE DEEP DIVE)
// ═════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addText("Inside CodeBuild — The Four Stages", {
    x: 0.5, y: 0.4, w: 12.3, h: 0.6, fontSize: 32, color: C.navy,
    fontFace: FONT_H, bold: true, margin: 0
  });
  s.addText("Each stage runs in an ephemeral container. Artifacts flow through S3 — stages are decoupled and independently retryable.", {
    x: 0.5, y: 1.0, w: 12.3, h: 0.4, fontSize: 14, color: C.textMd,
    fontFace: FONT_B, italic: true, margin: 0
  });

  const stages = [
    {
      num: "01", name: "BuildLayers", compute: "MEDIUM  •  4 vCPU  •  ~8 min",
      desc: "Cross-compiles Python packages for Lambda's Linux x86_64 runtime. Cannot be done on a Mac — binaries must match.",
      detail: "Pip cache in S3  →  ~6 min saved on re-runs"
    },
    {
      num: "02", name: "TerraformPlan", compute: "SMALL  •  2 vCPU  •  ~3 min",
      desc: "Runs terraform plan against S3-backed state. Produces a binary tfplan diff — exactly what will change in AWS.",
      detail: "No changes applied yet — safe to review"
    },
    {
      num: "03", name: "Approval Gate", compute: "MANUAL  •  SNS email",
      desc: "Pipeline pauses. Reviewer checks the plan output in CloudWatch logs, then approves or rejects.",
      detail: "The human safety net for production infra"
    },
    {
      num: "04", name: "TerraformApply", compute: "SMALL  •  2 vCPU  •  ~5 min",
      desc: "Applies the exact tfplan from stage 2 — no drift. Publishes Lambda versions and triggers CodeDeploy.",
      detail: "Exits by handing off to CodeDeploy"
    },
  ];

  const xs = [0.5, 3.71, 6.92, 10.13];
  stages.forEach((st, i) => {
    const x = xs[i];
    // Card
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: 1.7, w: 3.03, h: 4.8,
      fill: { color: C.cardBg }, line: { color: C.divider, width: 1 },
      shadow: mkShadow()
    });
    // Num label
    s.addText(st.num, {
      x: x + 0.2, y: 1.85, w: 1.0, h: 0.6, fontSize: 36,
      color: C.orange, bold: true, fontFace: FONT_H, margin: 0
    });
    // Stage name
    s.addText(st.name, {
      x: x + 0.2, y: 2.5, w: 2.7, h: 0.5, fontSize: 18,
      color: C.navy, bold: true, fontFace: FONT_H, margin: 0
    });
    // Compute label
    s.addText(st.compute, {
      x: x + 0.2, y: 3.05, w: 2.7, h: 0.35, fontSize: 10,
      color: C.blue, bold: true, fontFace: FONT_B, charSpacing: 2, margin: 0
    });
    // Divider
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: 3.45, w: 0.5, h: 0.03,
      fill: { color: C.orange }, line: { color: C.orange }
    });
    // Description
    s.addText(st.desc, {
      x: x + 0.2, y: 3.6, w: 2.7, h: 1.9, fontSize: 12,
      color: C.textMd, fontFace: FONT_B, valign: "top", margin: 0
    });
    // Detail callout
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: 5.75, w: 2.63, h: 0.6,
      fill: { color: C.lightBg }, line: { color: C.divider, width: 1 }
    });
    s.addText(st.detail, {
      x: x + 0.25, y: 5.75, w: 2.53, h: 0.6, fontSize: 10,
      color: C.textDk, italic: true, fontFace: FONT_B, valign: "middle", margin: 0
    });

    // Arrow between cards
    if (i < stages.length - 1) {
      s.addText("▶", {
        x: x + 3.03, y: 3.9, w: 0.18, h: 0.3, fontSize: 16,
        color: C.orange, align: "center", valign: "middle", bold: true, margin: 0
      });
    }
  });

  // Bottom callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 6.65, w: 12.33, h: 0.45,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  s.addText([
    { text: "KEY INSIGHT:  ", options: { color: C.orange, bold: true, fontSize: 12 } },
    { text: "S3 artifacts decouple stages. If apply fails, the plan artifact is still there — retry without rebuilding.",
      options: { color: "FFFFFF", fontSize: 12 } }
  ], { x: 0.8, y: 6.65, w: 12, h: 0.45, fontFace: FONT_B, valign: "middle", margin: 0 });

  addFooter(s, 4);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 5 — CODEDEPLOY CANARY + ROLLBACK
// ═════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.lightBg };

  s.addText("CodeDeploy — The Safety Net", {
    x: 0.5, y: 0.4, w: 12.3, h: 0.6, fontSize: 32, color: C.navy,
    fontFace: FONT_H, bold: true, margin: 0
  });
  s.addText("Gradual traffic shifting + CloudWatch alarms = automatic rollback when bad code reaches production.", {
    x: 0.5, y: 1.0, w: 12.3, h: 0.4, fontSize: 14, color: C.textMd,
    fontFace: FONT_B, italic: true, margin: 0
  });

  // LEFT column — traffic shift visualization
  s.addText("TRAFFIC SHIFT OVER TIME", {
    x: 0.5, y: 1.6, w: 6.3, h: 0.35, fontSize: 11, color: C.orange,
    bold: true, charSpacing: 4, fontFace: FONT_B, margin: 0
  });

  // Canary strategy card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.0, w: 6.3, h: 2.2,
    fill: { color: C.cardBg }, line: { color: C.divider, width: 1 }, shadow: mkShadow()
  });
  s.addText("CANARY  —  stocks-signal", {
    x: 0.7, y: 2.1, w: 6.0, h: 0.4, fontSize: 15, color: C.navy,
    bold: true, fontFace: FONT_H, margin: 0
  });
  s.addText("10% → new version for 5 min → 100% shift", {
    x: 0.7, y: 2.5, w: 6.0, h: 0.35, fontSize: 12, color: C.textMd,
    italic: true, fontFace: FONT_B, margin: 0
  });

  // Visual bar for canary
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 3.0, w: 5.9, h: 0.5,
    fill: { color: C.divider }, line: { color: C.divider }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 3.0, w: 0.59, h: 0.5,
    fill: { color: C.orange }, line: { color: C.orange }
  });
  s.addText("10%", {
    x: 0.7, y: 3.0, w: 0.59, h: 0.5, fontSize: 11, color: "FFFFFF",
    bold: true, align: "center", valign: "middle", fontFace: FONT_B, margin: 0
  });
  s.addText("90% old version (watching)", {
    x: 1.29, y: 3.0, w: 5.31, h: 0.5, fontSize: 11, color: C.textDk,
    align: "center", valign: "middle", fontFace: FONT_B, margin: 0
  });
  s.addText("Fast feedback  •  Low blast radius  •  5-min bake", {
    x: 0.7, y: 3.65, w: 6.0, h: 0.4, fontSize: 11, color: C.success,
    italic: true, bold: true, fontFace: FONT_B, margin: 0
  });

  // Linear strategy card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.35, w: 6.3, h: 2.2,
    fill: { color: C.cardBg }, line: { color: C.divider, width: 1 }, shadow: mkShadow()
  });
  s.addText("LINEAR  —  options-analysis", {
    x: 0.7, y: 4.45, w: 6.0, h: 0.4, fontSize: 15, color: C.navy,
    bold: true, fontFace: FONT_H, margin: 0
  });
  s.addText("+10% every 1 min → full shift over 10 minutes", {
    x: 0.7, y: 4.85, w: 6.0, h: 0.35, fontSize: 12, color: C.textMd,
    italic: true, fontFace: FONT_B, margin: 0
  });

  // Gradient-like visual for linear
  const lw = 5.9 / 10;
  for (let i = 0; i < 10; i++) {
    const opacity = 20 + (i * 8); // 20, 28, 36, ..., 92
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7 + (i * lw), y: 5.35, w: lw, h: 0.5,
      fill: { color: C.blue, transparency: 100 - opacity },
      line: { color: C.blue, transparency: 100 - opacity }
    });
  }
  s.addText("Gradual rollout  •  More observation time  •  Less aggressive", {
    x: 0.7, y: 6.0, w: 6.0, h: 0.4, fontSize: 11, color: C.success,
    italic: true, bold: true, fontFace: FONT_B, margin: 0
  });

  // RIGHT column — rollback flow
  s.addText("AUTOMATIC ROLLBACK FLOW", {
    x: 7.0, y: 1.6, w: 6.3, h: 0.35, fontSize: 11, color: C.orange,
    bold: true, charSpacing: 4, fontFace: FONT_B, margin: 0
  });

  // Flow steps
  const flow = [
    { t: "1", label: "Deployment begins",   sub: "New version gets traffic slice",      color: C.blue },
    { t: "2", label: "CloudWatch watches",  sub: "Lambda Errors metric, 1-min windows", color: C.blue },
    { t: "3", label: "Threshold exceeded",  sub: "e.g. > 3 errors in 2 periods",        color: C.danger },
    { t: "4", label: "Alarm fires",         sub: "CloudWatch → CodeDeploy",             color: C.danger },
    { t: "5", label: "Auto-rollback",       sub: "100% traffic returns to old version", color: C.success },
  ];
  flow.forEach((f, i) => {
    const y = 2.05 + (i * 0.95);
    // Number circle
    s.addShape(pres.shapes.OVAL, {
      x: 7.0, y: y, w: 0.55, h: 0.55,
      fill: { color: f.color }, line: { color: f.color }
    });
    s.addText(f.t, {
      x: 7.0, y: y, w: 0.55, h: 0.55, fontSize: 16, color: "FFFFFF",
      bold: true, align: "center", valign: "middle", fontFace: FONT_H, margin: 0
    });
    // Label
    s.addText(f.label, {
      x: 7.7, y: y - 0.02, w: 5.5, h: 0.35, fontSize: 14, color: C.navy,
      bold: true, fontFace: FONT_H, margin: 0
    });
    s.addText(f.sub, {
      x: 7.7, y: y + 0.3, w: 5.5, h: 0.3, fontSize: 11, color: C.textMd,
      fontFace: FONT_B, margin: 0
    });
  });

  addFooter(s, 5);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 6 — WHY THIS / TAKEAWAYS
// ═════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Orange accent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.3, h: 7.5, fill: { color: C.orange }, line: { color: C.orange }
  });

  s.addText("KEY TAKEAWAYS", {
    x: 0.7, y: 0.5, w: 12, h: 0.4, fontSize: 13, color: C.orange,
    bold: true, charSpacing: 6, fontFace: FONT_B, margin: 0
  });
  s.addText("Why This Architecture Wins", {
    x: 0.7, y: 0.95, w: 12, h: 0.8, fontSize: 36, color: "FFFFFF",
    bold: true, fontFace: FONT_H, margin: 0
  });

  // Takeaway cards in 2x3 grid
  const takeaways = [
    { icon: "⚡", title: "Fast & Reliable Triggers",
      body: "V2 pipelines use EventBridge with path filters — infra changes don't retrigger frontend, and vice versa." },
    { icon: "🛡", title: "Safety First",
      body: "Manual approval gate on infra. Canary deployments on critical Lambdas. Auto-rollback on CloudWatch alarms." },
    { icon: "♻", title: "Fully Repeatable",
      body: "Everything in Terraform — the pipeline defines itself. Destroy & recreate the entire stack from git." },
    { icon: "🔒", title: "Least Privilege",
      body: "Three separate IAM roles — CodePipeline, CodeBuild, CodeDeploy. Compromise of one doesn't cascade." },
    { icon: "💰", title: "Cost-Effective",
      body: "V2 pay-per-minute pricing: ~$0.70/month for our usage vs $2/month flat on V1. Pipelines pay for what they do." },
    { icon: "👀", title: "Observable",
      body: "CloudWatch logs per build. SNS notifications on approval. X-Ray traces on Lambdas. Everything is visible." },
  ];

  const cardW = 3.95, cardH = 2.35;
  takeaways.forEach((t, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.7 + col * (cardW + 0.15);
    const y = 2.0 + row * (cardH + 0.2);

    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: cardW, h: cardH,
      fill: { color: "2D3E52" }, line: { color: "3A4E66", width: 1 }
    });
    // Orange accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: 0.08, h: cardH,
      fill: { color: C.orange }, line: { color: C.orange }
    });
    // Icon
    s.addText(t.icon, {
      x: x + 0.2, y: y + 0.15, w: 0.7, h: 0.6, fontSize: 28,
      valign: "middle", fontFace: FONT_B, margin: 0
    });
    // Title
    s.addText(t.title, {
      x: x + 0.9, y: y + 0.2, w: cardW - 1.0, h: 0.5, fontSize: 16,
      color: "FFFFFF", bold: true, fontFace: FONT_H, valign: "middle", margin: 0
    });
    // Body
    s.addText(t.body, {
      x: x + 0.25, y: y + 0.85, w: cardW - 0.45, h: cardH - 1.0, fontSize: 12,
      color: "CADCFC", fontFace: FONT_B, valign: "top", margin: 0
    });
  });

  // Footer-like tagline
  s.addText("From git push to production, safely — in under 20 minutes.", {
    x: 0.7, y: 7.0, w: 12, h: 0.4, fontSize: 13, color: C.orange,
    italic: true, bold: true, fontFace: FONT_B, align: "center", margin: 0
  });
}

// Save
pres.writeFile({ fileName: "/Users/aryakirtisingh/intraday_trading/aws_devops_presentation.pptx" })
  .then(fn => console.log("Created:", fn));
