# 📈 AI-Powered Intraday Trading Assistant

**Real-time NSE/BSE stock analysis with institutional-grade AI signals.**

A fully serverless cloud platform combining technical analysis, news sentiment, and AI-powered recommendations. Deployed on AWS with 100% uptime, zero infrastructure overhead, and pay-as-you-go pricing (~$17–22/month for an active trading day user).


---

## 🎯 Why I Built This

My dad has been trading for years, but the process always frustrated me to watch. He'd have five browser tabs open on his phone — one for charts, one for news, one for a screener — switching between them constantly, trying to piece together a picture before the opportunity slipped away.

I built this so he has **one place to look**. Open the dashboard, see every stock's signal, read the news sentiment, and ask the AI a question — all without leaving the page. No subscriptions, no delays, no tab chaos.

> *A junior research analyst that works 24/7, costs ₹200/month, and never takes a lunch break.*

> This project is in **alpha** and actively evolving based on real trading feedback. Features and signals will improve over time.

### What Makes It Different

| Feature | Typical Trading Tools | This Platform |
|---------|----------------------|---------------|
| **Cost** | ₹500–2000/month | ~$17–22/month (60s intraday refresh + Bedrock AI) |
| **AI Chat** | None or basic | Ask anything in plain English, Claude Haiku 3.5 provides institutional analysis |
| **Signal Engine** | 2–3 indicators | 13 indicators + VWAP + ORB + support/resistance + 200-day SMA + Fibonacci + volume profile + FII/DII market bias + AI-validated + news sentiment (adaptive weighting) |
| **News Sentiment** | Separate tab / manual reading | Built into signal score — 6 RSS feeds auto-weighted by recency (intraday-tightened) + source authority |
| **Alerts** | None or paid add-on | Browser push notifications for wishlist stocks + signal tracking (hit rate %) |
| **Timeframes** | 15m or 1h minimum | **5-min + 15-min + daily** — cleanest entry signals on 5m, validated against daily trend |
| **Institutional Data** | None | FII/DII daily net buy/sell → market bias badge + signal score adjustment |
| **Data Source** | Paid APIs | 100% free (yfinance, NSE, 6 RSS feeds, Bedrock AI) |
| **Infrastructure** | Always-on servers | Serverless — scales to $0 when market is closed |
| **Index Strip** | Separate terminal / app | NIFTY 50, BANKNIFTY, India VIX live in the header — always visible |
| **R:R Ratio** | Manual calculation | Auto-calculated on every signal card from ATR-based targets |
| **Options Analysis** | Separate platform | PCR, IV percentile (with 1-day fallback), Greeks, max-pain — all in-dashboard |
| **Volume Profile** | Premium add-on | Horizontal bar chart POC (Point-of-Control) shown inline |
| **Risk Management** | Manual | Sector concentration warning + liquidity alerts + 2% risk position sizing |
| **Export** | Screenshot or manual | One-click Excel export of all 80 stocks |
| **Mobile** | Desktop-first | Mobile-responsive — browser notifications work on Android |

---

## ✨ Key Features

### 📊 Smart Stock Signals
- **80 Indian stocks** across 10 sectors (IT, Banking, Finance, Energy, Pharma, Auto, FMCG, Infra, Metals, Telecom) scored using 12 technical indicators + sentiment from 6 news sources + AI validation
- Uses **1 year of daily data** from yfinance — enough for 200-day moving averages and reliable long-term trend detection
- AI Signal Validator (Claude Haiku) reviews every signal, catches contradictions, flags risks
- AI Headline Classifier (Nova Micro) upgrades impactful news sentiment automatically
- Adaptive weighting adjusts technical vs sentiment ratio based on news volume
- Signals: **STRONG BUY / BUY / HOLD / SELL / STRONG SELL** with confidence scores + AI thesis
- **Relative Strength vs NIFTY 50** — identifies stocks outperforming/underperforming the index
- **ATR-based targets & stop-loss** with Bollinger Bands + pivot support/resistance
- **2% risk position sizing** on ₹100K portfolio

### ⚡ Progressive Loading with Pagination
- First 20 stocks load instantly (~3s), remaining stocks load in background
- Paginated view (20 stocks per page) with smooth navigation
- No more waiting for all 80 stocks — browse page 1 while pages 2–4 load behind the scenes
- Once all 80 stocks are loaded, **cards never vanish on refresh** — only the data inside updates (merge-in-place); no blank screen, no disappearing cards
- Sector filtering and free-form search across all loaded stocks

### 🤖 AI Chat (Claude Haiku 3.5 via Bedrock Agent)
- Ask in plain English: *"Should I buy RELIANCE today?"* or *"Compare TCS vs INFY"*
- AI calls the same signal engine you see on the dashboard — real analysis, not generic answers
- Powered by Claude Haiku 3.5 with **3 callable tools** (technical analysis, news sentiment, options data)
- Multi-step reasoning: analyzes 12 indicators + news + relative strength before answering
- Intent detection: stock analysis, comparisons, education, portfolio queries
- Multi-turn session memory across messages

### 📈 Options Analysis
- **Put-Call Ratio (PCR)** — >1.3 bullish (protection seeking), <0.7 bearish
- **IV Percentile** — High (>80%) sell premium, Low (<20%) buy options
- **Max-Pain Strike** — strike where combined OI loss is maximum
- **Greeks Calculator** — Delta, Gamma, Theta, Vega (Black-Scholes)
- **30-day rolling IV history** stored in DynamoDB (daily snapshots at market close)
- **3-tier fallback**: NSE API (curl_cffi TLS fingerprinting) → Yahoo Finance → Synthetic chain

### 💼 Portfolio Tracker
- Add holdings with buy price and quantity
- Live P&L calculation (day gain + total gain) using real-time prices
- Multiple lots per symbol supported (UUID-based holding IDs)
- Search and add any of the 80 tracked stocks via autocomplete

### 📰 Market News with Sentiment
- Aggregates news from **6 RSS feeds**: Economic Times, Moneycontrol, LiveMint, Business Standard, Yahoo Finance, Google News
- Each headline tagged **Bullish / Bearish / Neutral** using VADER NLP + 100+ finance domain lexicon
- **Source authority weighting**: ET/Moneycontrol (1.3x), Business Standard/LiveMint (1.2x)
- **Recency weighting** (intraday-tightened): ≤2h → 1.0, ≤4h → 0.70, ≤6h → 0.40, ≤12h → 0.20, older → 0.05
- AI Headline Classifier (Nova Micro) reclassifies top 3 headlines for impact (HIGH/MEDIUM/LOW)

### ⭐ Wishlist & Excel Export
- Bookmark stocks to a persistent watchlist (saved in DynamoDB with PITR backup)
- One-click Excel export with full analysis for all 80 stocks
- Styled XLSX: signal-based background colors, formatted headers, title + disclaimer

### 🔔 Real-Time Alerts & Signal Tracking
- **Browser Notifications** — instant popup when a wishlist stock flips to STRONG BUY/SELL (works on mobile too)
- **Signal Performance Tracking** — localStorage tracks every BUY signal, computes hit rate, shows accuracy badge
- **FII/DII Market Sentiment** — daily institutional buying/selling data from NSE; market bias badge (BEARISH/BULLISH/NEUTRAL) in header with score adjustments

### 📊 Advanced Charting & Technical Levels
- **Dual Timeframe Support** — switch between 5m and 15m intraday charts; cleaner entry signals on faster timeframes
- **Volume Profile Histogram** — horizontal bar chart showing volume-at-price; Point-of-Control (POC) highlighted in orange for institutional levels
- **Fibonacci Retracements** — 23.6%, 38.2%, 50%, 61.8% levels calculated from 52W high/low; shown in modal stats for swing trade targets
- **Multi-Timeframe Validation** — daily trend filters prevent STRONG BUY signals when daily price < SMA20; alerts "Against daily downtrend"
- **Liquidity Warnings** — stocks with low volume (< 30% of 20-day avg) flagged with reduced score; prevents slippage surprises

### 📈 Portfolio Risk Management
- **Sector Concentration Alert** — portfolio tab warns if any sector ≥40% of holdings; prevents correlated drawdowns
- **Trailing Stop Loss Badge** — "🔒 Raise stop to breakeven" reminder when profit ≥10% (roadmap: auto-update stops)
- **Position Sizing** — 2% risk per trade calculated automatically from ATR-based stops on ₹100K portfolio

### 🔐 Authentication (AWS Cognito)
- Login / Sign-up screen before the dashboard is accessible — no one can view data without an account
- Email + password sign-up with email verification (6-digit code)
- Persistent sessions using Cognito ID tokens (1-hour access token, 30-day refresh token — auto-renewed)
- Per-user wishlist and portfolio — every account sees only its own data
- Logout button in the header clears the session instantly
- All API routes protected by a JWT authorizer on API Gateway — unauthenticated requests get `401`

### 📉 Live Index Strip
- **NIFTY 50, BANKNIFTY, India VIX** displayed as a persistent strip below the header — always visible
- Shows last closing price when market is closed, live price during trading hours
- Colour-coded change % (green = up, red = down), refreshes every 5 minutes
- Fetched via Yahoo Finance v8 chart API (direct HTTP — no yfinance overhead, sub-3s response)

### ⚡ Top Movers Strip
- Horizontal scrolling pill strip showing the **biggest % movers** from the current stock analysis
- Always visible above the stock grid — no need to dig into tabs
- Each pill shows symbol, direction arrow, % change, and current price

### 📊 Compact Signal Pill Bar
- **5 signal-type counts** (STRONG BUY / BUY / HOLD / SELL / STRONG SELL) compressed into a single-row interactive pill bar — pushes the stock grid above the fold
- Each pill is **clickable** — tap 🟢 S.BUY to instantly filter to only STRONG BUY stocks
- Avg AI score badge and total stocks analysed shown inline
- Top 5 BUY picks by score shown as clickable chips beneath the bar

### 🔄 Signal Changed Badge
- Stocks that changed signal since the last refresh show an **↑ UPGRADED** (green) or **↓ DOWNGRADED** (red) badge on the card
- Detected client-side via localStorage snapshot — no extra API call

### 🎯 Risk:Reward Ratio on Every Card
- Each stock card shows **R:R ratio** (e.g. R:R 1:2.4) calculated from ATR-based target and stop-loss
- Colour-coded: green ≥ 2:1, amber ≥ 1:1, red < 1:1
- Signal timestamp shows when the analysis was last computed (IST)

### 📅 Day High / Low on Cards
- Each stock card shows today's **intraday High and Low** (from 15-min bars) alongside the current price
- **ORB tag** (🟣 ORB) appears on cards where an Opening Range Breakout has been detected

### 🔃 Sort Bar
- Sort the stock grid by: **⭐ Score** (default) | **🎯 R:R ratio** | **📈 Change%** | **📊 Volume**
- Clicking a sector filter automatically resets the signal filter to "All" — so Banking / Finance / etc. always show stocks regardless of market conditions

### 🕐 Smart Auto-Refresh
- IST market hours indicator (9:15 AM – 3:30 PM, weekdays)
- **Dynamic refresh interval**: 60 seconds during market hours, 5 minutes after hours — so you never miss a fast intraday move
- **Tab-visibility guard**: refresh pauses automatically when you minimise or switch away from the tab — saves ~60% of Lambda compute cost with zero UX impact
- Refresh interval badge shows current mode (`1m` / `5m`) next to the countdown
- Every refresh fetches **live data directly** — no stale cache, prices always reflect current market
- **Stale-while-revalidate architecture**: on every refresh cycle, existing stock cards stay visible immediately; fresh data is merged in-place as each page arrives — no blanking, no 30-second waits
- **Overlap-safe**: the background refresh guard stays active until all 4 pages finish loading, preventing overlapping refreshes if a cycle runs long

---

## 🔄 AWS DevOps Pipeline (v3.0)

The project now uses a fully AWS-native CI/CD pipeline replacing GitHub Actions for deployments.

### Architecture

```
GitHub (source — stays as-is)
    │
    │  git push to main
    ▼
AWS CodeStar Connection (GitHub v2 OAuth App)
    │
    ├──[infrastructure/** lambdas/** backend/** prompts/**]──▶ trading-infra-pipeline
    │       Stage 1: Source        (GitHub → ZIP artifact)
    │       Stage 2: BuildLayers   (CodeBuild: build_layers.sh + zip handlers)
    │       Stage 3: TerraformPlan (CodeBuild: terraform plan → tfplan artifact)
    │       Stage 4: Approval      (Manual gate — SNS email to owner)
    │       Stage 5: TerraformApply(CodeBuild: terraform apply + CodeDeploy trigger)
    │
    └──[frontend/**]──────────────────────────────────────▶ trading-frontend-pipeline
            Stage 1: Source
            Stage 2: Deploy  (CodeBuild: s3 sync + CloudFront invalidation)

CodeDeploy — Safe Lambda Traffic Shifting
    trading-lambda-app
    ├── trading-stocks-signal-dg    → LambdaCanary10Percent5Minutes
    │     10% traffic to new version → 5 min bake → 100% shift (or auto-rollback)
    └── trading-options-analysis-dg → LambdaLinear10PercentEvery1Minute
          +10% traffic every 1 min → full shift in 10 min (or auto-rollback)
```

### AWS DevOps Services Added

| Service | Resource | Purpose |
|---------|----------|---------|
| **CodePipeline** | `trading-infra-pipeline` | 5-stage infra deployment orchestration |
| **CodePipeline** | `trading-frontend-pipeline` | 2-stage frontend deployment |
| **CodeBuild** | `trading-build-layers` | Builds Lambda layers + zips all 14 handlers |
| **CodeBuild** | `trading-terraform-plan` | Runs `terraform plan`, outputs tfplan artifact |
| **CodeBuild** | `trading-terraform-apply` | Runs `terraform apply` + triggers CodeDeploy |
| **CodeBuild** | `trading-frontend-deploy` | S3 sync + CloudFront invalidation |
| **CodeDeploy** | `trading-lambda-app` | Lambda deployment application |
| **CodeDeploy** | `trading-stocks-signal-dg` | Canary 10%/5min for stocks-signal |
| **CodeDeploy** | `trading-options-analysis-dg` | Linear 10%/1min for options-analysis |
| **CodeStar Connections** | `trading-github-connection` | OAuth bridge: GitHub → AWS (no PAT needed) |
| **SNS** | `trading-pipeline-approvals` | Email approval notification before terraform apply |
| **SSM Parameter Store** | `/trading/*` | Secure config for CodeBuild (bucket names, IDs) |
| **CloudWatch Alarms** | `trading-*-errors` | Triggers automatic CodeDeploy rollback on error spike |
| **Lambda Aliases** | `:live` alias | Traffic shifting target for CodeDeploy on 2 functions |
| **X-Ray** | All 14 Lambda functions | Distributed tracing — shows exactly where latency comes from |

### How CodeDeploy Traffic Shifting Works

```
Before deployment:   live alias → v6 (100% traffic)

During canary:       live alias → v6 (90%) + v7 (10%)
                     ↑ 5-minute bake window
                     If CloudWatch alarm fires → auto-rollback to v6

After bake:          live alias → v7 (100% traffic)
```

API Gateway now calls the `:live` alias instead of `$LATEST`, so traffic shifting happens transparently without any API Gateway changes.

### New Files Added

```
infrastructure/
├── terraform/
│   ├── codebuild.tf       ← 4 CodeBuild projects + SSM parameters
│   ├── codepipeline.tf    ← 2 pipelines, CodeStar connection, SNS, artifact S3
│   ├── codedeploy.tf      ← CodeDeploy app, deployment groups, Lambda aliases, alarms
│   └── iam_devops.tf      ← IAM roles for CodePipeline, CodeBuild, CodeDeploy
├── buildspec/
│   ├── buildspec-layers.yml           ← Build Lambda layers + zip handlers
│   ├── buildspec-terraform-plan.yml   ← terraform plan
│   ├── buildspec-terraform-apply.yml  ← terraform apply + CodeDeploy trigger
│   └── buildspec-frontend.yml         ← S3 sync + CloudFront invalidation
└── appspec/
    ├── appspec-stocks-signal.yml      ← CodeDeploy AppSpec template
    └── appspec-options-analysis.yml   ← CodeDeploy AppSpec template
```

---

## 🚀 Latest Improvements (v2.0)

### ✅ 15 Critical Enhancements Shipped

#### **1. RSS Feed Timeout Protection** 🔴→✅
- **Issue**: `feedparser.parse()` had no timeout — if any of the 6 RSS feeds hung, the entire Lambda could hit the 29s timeout and crash signal generation
- **Fix**: Added `_parse_feed(url, timeout=5)` wrapper in `sentiment_agent.py` with urllib timeout control
- **Impact**: Eliminates Lambda crashes from stuck RSS feeds; graceful fallback to empty sentiment on timeout

#### **2. Browser Push Notifications** 🔔
- **Issue**: No alerting system — had to keep the tab open 24/7 to catch a STRONG BUY signal
- **Fix**: Added `_notifyWishlistChanges()` function + browser Notification API with permission request on login
- **Impact**: Instant popup notification when a wishlist stock upgrades/downgrades signal. Works on desktop/Android

#### **3. Signal Performance Tracking** 📊
- **Issue**: No backtesting — no way to know if signals have historically worked
- **Fix**: Added `_trackSignalPerformance()` logging all BUY signals to localStorage, tracking target/stop hits, computes accuracy
- **Impact**: Signal Accuracy badge shows hit rate %. Users can see which signal types (MACD crossover, ORB, etc.) are most reliable

#### **4. 5-Minute Intraday Chart Support** ⏱️
- **Issue**: Only 15m bars were available; most scalpers need 5m or 1m data
- **Fix**: Added parallel `yfinance` call for 5m bars in `stock_fetcher.py`, rendered via new "5m" chart timeframe toggle in frontend
- **Impact**: Cleaner ORB + VWAP retest setups visible on 5m. Users can switch between 5m ↔ 15m on modal chart

#### **5. NIFTY 50 Column Guard** 🛡️
- **Issue**: If yfinance returned unexpected schema for ^NSEI, RS ratio calculation failed silently with KeyError
- **Fix**: Added `"Close" in hist.columns` validation before RS ratio computation in `signal_agent.py`
- **Impact**: Graceful fallback to neutral RS adjustment if NIFTY data is malformed; no crash

#### **6. Trailing Stop-Loss Logic** 📈
- **Issue**: Static stops calculated at signal time never trailed; stock could hit stop then rocket upward
- **Fix**: Added "🔒 Raise stop to breakeven" badge on holdings with ≥10% unrealised gain in portfolio
- **Impact**: Visual cue to manually trail stops. Roadmap: auto-update DynamoDB schema for fully automated TSL

#### **7. Custom Stock Universe** 🔍
- **Issue**: Fixed 80-stock list; couldn't trade breakouts in mid-caps like IREDA, RAIL VIK
- **Fix**: Added "🔍 Analyse any NSE stock →" fallback in search bar when no known stocks match
- **Impact**: Users can now analyze ANY NSE/BSE symbol on-demand — search bar calls `/api/stock/{symbol}` directly

#### **8. Multi-Timeframe Trend Confirmation** 🔄
- **Issue**: 15m BUY signals in strong daily downtrends were dangerous fades
- **Fix**: Added daily trend alignment check in `technical_agent.py` — if score > 55 but daily price < SMA20, reduce by 8pts; if daily bullish, add 5pts bonus
- **Impact**: Eliminates high-probability false signals by validating against daily trend. More reliable swing trades

#### **9. Liquidity & Slippage Warning** ⚠️
- **Issue**: Position sizing assumed perfect fills; thin stocks (IDEA, NATIONALUM) had 1-2% fill slippage
- **Fix**: Added volume check in `technical_agent.py` — if volume < 30% of 20-day avg, reduce score by 5 and flag "Low liquidity"
- **Impact**: Prevents entry into illiquid symbols. Protects against slippage on actual trade entry

#### **10. Portfolio Sector Concentration Warning** 📊
- **Issue**: Max per-trade risk enforced (2% rule) but no check for sector concentration (e.g., 30% in Banking)
- **Fix**: Added `_renderSectorRiskWarning(holdings)` in portfolio tab — calculates % per sector, warns if any ≥40%
- **Impact**: Visual red warning: "⚠️ Banking: 45% — too concentrated!" Prevents correlated drawdowns

#### **11. Volume Profile Chart** 📈
- **Issue**: VWAP shown but no volume-at-price histogram — institutional support/resistance levels invisible
- **Fix**: Added `_renderVolumeProfile(s)` function computing 12 price buckets, rendering horizontal bar chart via Chart.js
- **Impact**: Point-of-Control (POC) highlighted in orange. Users see which price levels had highest volume — natural support/resistance

#### **12. Fibonacci Retracement Levels** 📐
- **Issue**: No Fibonacci levels despite having 1-year H/L data
- **Fix**: Added `fib_levels` dict in `signal_agent.py` with 23.6%, 38.2%, 50%, 61.8% retracements from 52W high/low
- **Impact**: Modal stats now show Fib targets. Swing traders can set stop-losses and targets using Fibonacci zones

#### **13. FII/DII Market Sentiment Data** 🏛️
- **Issue**: Foreign/Domestic Institutional Investor flow is the single biggest intraday market driver — completely absent
- **Fix**: New Lambda `trading_fii_dii` fetches NSE public endpoint `/api/fiidiiTradeReact` daily, returns market_bias + fii_net + score_modifier
- **Impact**: FII/DII badge in header shows "BEARISH (₹2000Cr sold)" or "BULLISH (₹1500Cr bought)". Signal scores auto-adjusted by -8 to +5 based on FII flow

#### **14. IV Percentile Bootstrap Fallback** ⚡
- **Issue**: New symbols showed "⚠️ Coming soon" for 5 days waiting for _MIN_READINGS
- **Fix**: Removed _MIN_READINGS hard requirement in `iv_history_store.py`. Now returns early estimate with label "⚠️ Early estimate (2/5 days)"
- **Impact**: Options data available instantly on Day 1 instead of Day 5+. Label makes uncertainty transparent to user

#### **15. ORB Session Caching** 🔐
- **Issue**: Opening Range Breakout (ORB) values reset incorrectly if user refreshed mid-session
- **Fix**: Added `_saveOrb(symbol, orb_high, orb_low)` and `_loadOrb(symbol)` functions using localStorage with date matching
- **Impact**: ORB values persist across page refreshes. Accurate intraday ORB tracking throughout the trading day

---

## 🔄 How It Works

```
User opens website
      │
      ↓
CloudFront serves static files from nearest edge (< 50ms)
      │
      ↓
Login screen — Cognito authenticates user, issues ID token
      │
      ↓
Frontend requests first 20 stocks → API Gateway (JWT authorizer validates token)
      │                                              │
      │                                    Batch fetch live prices from yfinance
      │                                              │
      │                                    Run 12 technical indicators
      │                                    + sentiment analysis + AI validation
      │                                              │
      ↓                                              ↓
Page 1 renders (~5–15s)             Background: fetch remaining stocks
      │                              (pages 2–4 load silently)
      ↓
User browses, clicks stock → modal with intraday chart + full analysis
      │                       (all prices are live — no stale cache)
      ↓
User asks AI → Bedrock Agent calls 3 tools → returns reasoned analysis
```

**EventBridge Schedules (1 automated job remaining):**
- **Daily 3:40 PM IST**: Snapshot ATM IV for 30-day rolling percentile history

> **Note:** Stock signal warmup and options cache warmup schedules were removed. All analysis now fetches live data on every request so prices and recommendations always reflect the current market.

---

## 🏗️ Technical Architecture

### High-Level System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER (Phone/Desktop)                      │
│                      CloudFront CDN (Mumbai Edge)                 │
│                      HTTP/2 + HTTP/3 | Static caching             │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              AWS Cognito User Pool                                 │
│     Email/password auth │ JWT ID tokens │ 30-day refresh          │
└──────────────────────┬───────────────────────────────────────────┘
                       │ ID Token (JWT)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    API Gateway (HTTP v2)                           │
│      16 Routes │ JWT Authorizer │ 29s timeout │ CORS enabled       │
└──────┬───────┬────────┬────────┬────────┬────────┬──────────────┘
       │       │        │        │        │        │
       ▼       ▼        ▼        ▼        ▼        ▼
   ┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐
   │Signal ││News   ││Options││Chat   ││Wishlist││Export │  ← 13 Lambdas
   │Engine ││Sentmnt││Chain  ││(Agent)││CRUD   ││Excel  │     (Python 3.12)
   └───┬───┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘
       │        │        │        │        │        │
       ▼        ▼        ▼        ▼        ▼        ▼
  ┌─────────────────────────────────────────────────────┐
  │              Shared Lambda Layers (4)                  │
  │  backend-layer │ heavy-layer  │ nlp-layer │ export   │
  │  (agents,utils)│(pandas,numpy │(VADER,RSS)│(openpyxl)│
  │                │ ta,yfinance, │           │          │
  │                │ scipy)       │           │          │
  └────────────────┴──────────────┴───────────┴──────────┘
       │                                          │
       ▼                                          ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │DynamoDB  │  │DynamoDB  │  │DynamoDB  │
  │Wishlist  │  │Portfolio │  │IV History│
  │(PITR)    │  │(PITR)    │  │(31d TTL) │
  └──────────┘  └──────────┘  └──────────┘
       │             │
       └──── user_id = Cognito sub (per-user data isolation)
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │     External Data Sources (ALL FREE)                  │
  │  Yahoo Finance  │  NSE Public API  │  6 RSS Feeds    │
  │  (prices, OHLCV)│  (options chain) │  (news headlines)│
  │  fetched LIVE on every request — no caching          │
  └──────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │     AWS Bedrock (GenAI Layer)                         │
  │  Claude 3.5 Haiku        │  Amazon Nova Micro        │
  │  • Signal validation     │  • Headline classification│
  │  • AI Chat (3 tools)     │  • $0.035/1M tokens       │
  │  • $0.25/1M input tokens │                           │
  └──────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │     EventBridge Scheduler (1 Automated Job)           │
  │  Daily 3:40PM IST : Snapshot IV for 30-day percentile│
  │  (warmup schedules removed — all data is live)       │
  └──────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │     S3 Buckets (2)                                    │
  │  SPA Hosting (private, CloudFront-only OAI access)   │
  │  Excel Exports (pre-signed URLs, 1-hour expiry)      │
  └──────────────────────────────────────────────────────┘
```

### Signal Generation Pipeline

```
Yahoo Finance (1yr daily + intraday 5m & 15m bars)
        │
        ▼
┌─── TECHNICAL AGENT ────────────────────────────────────┐
│  12 Indicators → Score 0–100                           │
│                                                        │
│  RSI (±20)  │ MACD crossover (±15) │ Bollinger (±15)    │
│  EMA 9/21 (±15) │ SMA 20/50 (±10)  │ SMA 200 (±8)    │
│  Golden/Death Cross (±6/±12)  │ Volume z-score (±10)  │
│  ADX (±8)   │ Stochastic RSI (±8)  │ RSI Div (±12)   │
│  VWAP (±8)  │ ORB (±6/±10)  │ Support/Resistance (±5)│
│                                                        │
│  + Relative Strength vs NIFTY 50 (±5)                 │
└─────────────────┬──────────────────────────────────────┘
                  │
6 RSS Feeds       │
        │         │
        ▼         │
┌─── SENTIMENT AGENT ───────────────────────────────────┐
│  Step 1: VADER base score per headline                 │
│  Step 2: Finance lexicon boost (100+ custom terms)     │
│  Step 3: Regex pattern detection (%, growth, decline)  │
│  Step 4: Nova Micro reclassifies top 3 headlines       │
│  Step 5: Recency × Source Authority weighting          │
│                                                        │
│  Output: -50 (bearish) to +50 (bullish)               │
└─────────────────┬──────────────────────────────────────┘
                  │
                  ▼
┌─── SIGNAL AGENT (Orchestrator) ───────────────────────┐
│                                                        │
│  Adaptive Weighting (based on sentiment strength):     │
│  ┌─────────────────────────────────────────────┐      │
│  │ Strong news (≥25)  → Tech 55% / Sent 45%   │      │
│  │ Moderate news (≥12)→ Tech 65% / Sent 35%   │      │
│  │ Weak news (<12)    → Tech 75% / Sent 25%   │      │
│  └─────────────────────────────────────────────┘      │
│                                                        │
│  Tanh S-curve: normalizes [-50,+50] → [0,100]        │
│  + Relative Strength vs NIFTY 50 adjustment           │
│  + ATR-based Stop-Loss & Target levels                │
│  + 2% risk position sizing (on ₹100K portfolio)       │
│                                                        │
│  → Final Score 0–100 → Signal Label                   │
│  → Risk Level (LOW / MEDIUM / HIGH from volatility)   │
└─────────────────┬──────────────────────────────────────┘
                  │
                  ▼
┌─── AI VALIDATOR (Claude 3.5 Haiku) ───────────────────┐
│  Reads ALL pre-computed indicators (never invents data)│
│  Returns:                                              │
│  • Thesis (3-line reasoning)                          │
│  • Agrees/disagrees with signal                       │
│  • Confidence level                                   │
│  • Risk flags & contradictions                        │
│  • e.g. "MACD says BUY but RSI says overbought"      │
└────────────────────────────────────────────────────────┘
```

### AI Chat Architecture (Bedrock Agent with Tool-Use)

```
User: "Should I buy RELIANCE today?"
        │
        ▼
┌─── BEDROCK AGENT (Claude 3.5 Haiku) ─────────────────┐
│  System prompt: TradingGuru persona                    │
│  Intent detection → decides which tools to call        │
│                                                        │
│  Available Tools:                                      │
│  ┌────────────────────────────────────────────────┐   │
│  │ 🔧 Technical Tool → 12 indicators for symbol  │   │
│  │ 🔧 Sentiment Tool → news headlines + score    │   │
│  │ 🔧 Options Tool   → PCR, IV, Greeks, max-pain │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  Multi-step reasoning → combined analysis              │
│  Session memory across messages                        │
│  Follow-up suggestions appended                        │
└───────────────────────────────────────────────────────┘
```

### Lambda Functions (14 Total)

| Function | Purpose | Timeout | Layers |
|----------|---------|---------|--------|
| `trading_stocks_signal` | Core signal engine + AI validator | 29s | backend, heavy, nlp |
| `trading_bedrock_chat` | AI Chat endpoint (Bedrock Agent) | 28s | backend |
| `trading_bedrock_technical_tool` | Tool: stock technical analysis | 15s | backend, heavy |
| `trading_bedrock_sentiment_tool` | Tool: news sentiment analysis | 20s | backend, nlp |
| `trading_bedrock_options_tool` | Tool: options chain analysis | 15s | backend, heavy |
| `trading_options_analysis` | Options chain API endpoint | 30s | backend, heavy |
| `trading_options_refresh` | Daily IV history snapshot (market close) | 30s | backend, heavy |
| `trading_news_sentiment` | News aggregation endpoint | 20s | backend, nlp |
| `trading_wishlist` | Wishlist CRUD operations | 10s | backend |
| `trading_portfolio` | Holdings P&L tracker | 10s | backend |
| `trading_market_status` | IST market hours + NIFTY 50 / BANKNIFTY / India VIX live prices | 15s | backend (stdlib only — no yfinance) |
| `trading_excel_export` | XLSX generation + pre-signed S3 URL | 10s | backend, export |
| `trading_fii_dii` | GET /api/fii-dii — FII/DII market sentiment data from NSE | 10s | backend |
| `trading_cache_clear` | Manual cache invalidation | 5s | backend |

### DynamoDB Tables (3)

| Table | PK | SK | TTL | Purpose |
|-------|----|----|-----|---------|
| `trading-wishlist` | `user_id` (Cognito sub) | `symbol` | — | Per-user watchlist (PITR enabled) |
| `trading-portfolio` | `user_id` (Cognito sub) | `holding_id` | — | Per-user holdings with buy price/qty (PITR enabled) |
| `trading-iv-history` | `symbol` | `date` | 31 days | 30-day rolling IV percentile snapshots |

> The `trading-cache` table (previously used for 15-min stock signal caching) is no longer written to for stock analysis. All signals are computed fresh on every request.

### Data Sources (All Free)

| Data | Source | Refresh Rate | Notes |
|------|--------|-------------|-------|
| Stock Prices (OHLCV) | Yahoo Finance (yfinance) | Real-time | Covers NSE + BSE, batch download for 80 stocks |
| 1-Year Daily History | Yahoo Finance | Daily | For 200-day SMA + all indicator calculations |
| 15-min Intraday Bars | Yahoo Finance | Intraday | For VWAP calculation + mini-charts |
| 5-min Intraday Bars | Yahoo Finance | Intraday | For faster entry signals (ORB, VWAP retest) on 5m timeframe |
| News Headlines | 6 RSS Feeds (ET, MC, BS, LM, Yahoo, Google) | Every 2–5 min | Weighted by source authority + recency (intraday-tightened) |
| Options Chain | NSE Public API (curl_cffi TLS fingerprint) | Real-time | Fallback: Yahoo Finance → Synthetic chain |
| FII/DII Data | NSE Public API (`fiidiiTradeReact`) | Daily (9:40 AM) | Foreign/Domestic Institutional Investor net buy/sell activity; market bias modifier |
| NIFTY 50 Index | Yahoo Finance | Real-time | Shared fetch for relative strength calculation |
| Market Status | Local IST time | Hardcoded | 9:15 AM – 3:30 PM IST, weekdays |
| NIFTY 50 / BANKNIFTY / India VIX | Yahoo Finance v8 chart API (direct HTTP) | Every 5 min | Shown in index strip — last close when market is closed, live during hours |

---

## 🛠️ Tech Stack

| Layer | Technology | Why This Choice |
|-------|-----------|-----------------|
| **Frontend** | HTML5 + Bootstrap 5 + Chart.js (vanilla JS) | No framework overhead — loads in <3s on mobile, zero build step |
| **Auth** | AWS Cognito + amazon-cognito-identity-js | Managed auth — email verification, JWT tokens, auto-refresh, per-user data |
| **Backend** | 13 Lambda functions (Python 3.12) | Serverless — ₹0 when market closed. Python for pandas/numpy/ta ecosystem |
| **Database** | DynamoDB (PAY_PER_REQUEST) | Zero admin, free tier (25 RCU/WCU), auto-scales |
| **AI** | Claude Haiku 3.5 + Nova Micro (Bedrock) | Haiku: fast (1-2s), cheap ($0.25/1M tokens). Nova: headlines only ($0.035/1M) |
| **API** | API Gateway HTTP v2 (16 routes + JWT authorizer) | Low latency, 29s timeout, native Cognito JWT validation |
| **CDN** | CloudFront (Mumbai edge) | HTTP/2+3, caching, S3 origin access identity |
| **Data** | yfinance, NSE API, 6 RSS feeds — fetched live | 100% free, always-fresh — no caching layer for stock signals |
| **IaC** | Terraform (10+ modules) | Reproducible, state management, multi-resource orchestration |
| **CI/CD** | AWS CodePipeline + CodeBuild + CodeDeploy | AWS-native pipeline: build → plan → manual approval → apply → canary deploy |
| **Tracing** | AWS X-Ray (all 14 Lambdas) | Distributed traces — flame graphs showing where latency comes from |
| **Scheduling** | EventBridge Scheduler (1 job) | Daily IV history snapshot only — no warmup needed without cache |
| **NLP** | VADER + 100+ finance lexicon + regex patterns | Free, fast, no API call needed for base sentiment |
| **Prompts** | YAML templates + Jinja2 (prompt_loader.py) | Versioned, testable, separated from code |

---

## 📊 Signal Algorithm

### 12 Technical Indicators (1 year of daily data)

| Indicator | Period | Signal Weight | What It Detects |
|-----------|--------|--------------|-----------------|
| **RSI** | 14 | ±20 | Oversold (<30) / Overbought (>70), ADX-aware context |
| **MACD** | 12,26,9 | ±15 | Signal line crossover — momentum shift |
| **Bollinger Bands** | 20, 2σ | ±15 | Price at band edges — mean reversion zones |
| **EMA 9/21** | 9, 21 | ±15 | Short-term trend crossover (fresh vs continuation) |
| **RSI Divergence** | — | ±12 | Price makes lower low but RSI makes higher low |
| **SMA 20/50** | 20, 50 | ±10 | 20>50 = uptrend, price above 20 = momentum |
| **Volume Z-Score** | 20-day | ±10 | >2σ = conviction, <-1σ = weak move |
| **ADX** | 14 | ±8 | Trend strength (>25 trending, <20 ranging) + direction |
| **Stochastic RSI** | 14, K=3, D=3 | ±8 | K/D crossovers in oversold/overbought zones |
| **SMA 200** | 200 | ±8 | Long-term trend filter |
| **VWAP** | Intraday | ±8 | Intraday fair value — above = bullish |
| **ORB (Opening Range Breakout)** | First 15m candle | ±6/±10 | Price above/below first candle; +10 if volume-confirmed |
| **Golden/Death Cross** | 50 vs 200 | ±6/±12 | Volume-confirmed 50-day vs 200-day crossover |
| **Support/Resistance** | Pivot points | ±5 | Price near nearest S1/S2/R1/R2 — bounce/rejection zones |
| **Relative Strength** | vs NIFTY 50 | ±5 | RS = (1+stock_return)/(1+nifty_return) — >1.2 outperforming |

### Daily Trend Filter (Multi-Timeframe Validation)
- Before generating a 15m intraday signal, system checks daily price vs daily SMA20
- **BUY on 15m but price < SMA20 on daily?** → Signal downgraded to HOLD; marked "Against daily trend"
- **BUY on 15m AND price > SMA20 on daily?** → Bonus +5 points; marked "Daily trend aligned"
- **STRONG BUY in strong daily downtrend** → Immediately suspect; high fade probability

### AI Signal Validator (Claude Haiku 3.5)
- Receives all 12 indicators + sentiment score + relative strength vs NIFTY 50 + daily trend alignment + liquidity check
- Validates the BUY/SELL/HOLD signal, identifies contradictions, flags risks
- Returns: thesis, confidence level, risk warnings, conflicting signals
- **Never invents data** — only reasons about pre-computed indicators

### Sentiment Analysis (6 RSS feeds + 2 AI models)

**3-Step Scoring Pipeline:**
1. **VADER base score** per headline
2. **Finance lexicon boost** — 100+ custom terms (e.g., "breakout" +2.5, "crash" -3.0, "earnings beat" +2.5)
3. **Regex pattern detection** — "grew 25%" → +0.1, "fell 15%" → -0.1

**AI Enhancement:**
- Top 3 headlines reclassified by **Nova Micro** for sentiment + impact level
- HIGH impact headlines get weight boost

**Weighting:**
- **Recency** (intraday-tightened): ≤2h → 1.0, ≤4h → 0.70, ≤6h → 0.40, ≤12h → 0.20, older → 0.05 — stale headlines have near-zero weight
- **Source authority**: ET/MC → 1.3x, BS/LM → 1.2x, others → 1.0x
- Combined: recency × authority

**Final Score:** -50 (bearish) to +50 (bullish)

### Final Signal (Adaptive Weighting)
```
Sentiment Strength     Tech Weight    Sentiment Weight
─────────────────      ───────────    ────────────────
Strong (≥25)           55%            45%
Moderate (≥12)         65%            35%
Weak (<12)             75%            25%

Normalization: Tanh S-curve [-50,+50] → [0,100]

Final Score = Tech × weight + Sentiment × weight ± RS adjustment

Thresholds:
  > 70   → STRONG BUY   🟢🟢
 55–70   → BUY          🟢
 40–55   → HOLD         🟡
 25–40   → SELL         🔴
  < 25   → STRONG SELL  🔴🔴
```

---

## 📁 Project Structure

```
intraday_trading/
├── README.md
├── requirements.txt
├── run.py                              ← Local dev startup script
│
├── backend/                            ← Core business logic (shared: Lambda + local)
│   ├── app.py                          ← FastAPI app (local dev, 15 routes)
│   ├── prompt_loader.py                ← Jinja2 YAML prompt template renderer
│   ├── agents/
│   │   ├── signal_agent.py             ← Master orchestrator (tech + sentiment + RS)
│   │   ├── technical_agent.py          ← 12 indicators + VWAP + support/resistance
│   │   ├── sentiment_agent.py          ← VADER + 6 RSS feeds + Nova Micro classifier
│   │   └── options_agent.py            ← Options chain analysis (PCR, IV, Greeks, max-pain)
│   ├── data/
│   │   ├── stock_fetcher.py            ← Yahoo Finance (batch download, 1yr + intraday)
│   │   ├── options_fetcher.py          ← NSE API (curl_cffi TLS fingerprint) + fallbacks
│   │   └── playwright_fetcher.py       ← Browser automation (deprecated in Lambda)
│   └── utils/
│       ├── excel_exporter.py           ← Styled XLSX export (openpyxl)
│       ├── greeks.py                   ← Black-Scholes Greeks calculator
│       ├── iv_history_store.py         ← 30-day rolling IV history (DynamoDB)
│       └── wishlist_store.py           ← Wishlist persistence
│
├── frontend/                           ← Single-Page App (S3 + CloudFront)
│   ├── index.html                      ← 4-tab SPA (Intraday | Wishlist | Chat | Portfolio)
│   ├── css/style.css                   ← Bootstrap 5 + custom styling
│   └── js/app.js                       ← ~2000 lines vanilla JS (progressive loading, pagination, modals)
│
├── lambdas/                            ← AWS Lambda handlers (13 functions)
│   ├── trading_stocks_signal/          ← Core signal engine + AI validator
│   │   ├── handler.py                  ← API: /api/stocks, /api/stock/{symbol}
│   │   └── ai_validator.py             ← Bedrock call: signal thesis + confidence
│   ├── trading_bedrock_chat/           ← AI Chat (Haiku 3.5 with tool-use)
│   ├── trading_bedrock_technical_tool/ ← Tool: technical analysis (callable by agent)
│   ├── trading_bedrock_sentiment_tool/ ← Tool: sentiment analysis (callable by agent)
│   ├── trading_bedrock_options_tool/   ← Tool: options analysis (callable by agent)
│   ├── trading_options_analysis/       ← Options chain API endpoint
│   ├── trading_options_refresh/        ← EventBridge warmup (2 min) + IV history
│   ├── trading_news_sentiment/         ← News aggregation endpoint
│   ├── trading_wishlist/               ← Wishlist CRUD operations
│   ├── trading_portfolio/              ← Portfolio P&L tracking
│   ├── trading_market_status/          ← Market hours (IST)
│   ├── trading_excel_export/           ← Pre-signed S3 URL generation
│   ├── trading_cache_clear/            ← Manual cache invalidation
│   └── shared/                         ← Shared utilities (bundled into layers)
│       ├── prompt_loader.py            ← Prompt template rendering
│       └── dynamo_cache.py             ← DynamoDB cache helper
│
├── prompts/                            ← AI prompt templates (YAML + Jinja2)
│   ├── signal_validator.yaml           ← Claude Haiku signal validation prompt
│   ├── headline_classifier.yaml        ← Nova Micro headline impact classification
│   ├── trading_guru_agent.txt          ← Bedrock Agent system instruction
│   └── _partials/                      ← Modular prompt fragments
│
└── infrastructure/                     ← Terraform IaC + Lambda layers
    ├── terraform/
    │   ├── main.tf                     ← Terraform config & AWS provider
    │   ├── variables.tf                ← Input vars (region, account, model IDs)
    │   ├── locals.tf                   ← Computed locals (table names, prefixes)
    │   ├── api_gateway.tf              ← HTTP API v2 (16 routes + Cognito JWT authorizer)
    │   ├── cognito.tf                  ← Cognito User Pool, App Client, JWT Authorizer
    │   ├── lambda_functions.tf         ← 13 Lambda function definitions + layers
    │   ├── lambda_layers.tf            ← Layer archiving (pandas, numpy, ta, VADER, etc.)
    │   ├── dynamodb.tf                 ← 4 tables: cache, wishlist, portfolio, iv_history
    │   ├── eventbridge.tf              ← 3 schedules: warmup, options refresh, IV snapshot
    │   ├── s3.tf                       ← 2 buckets: SPA hosting + Excel exports
    │   ├── cloudfront.tf               ← CDN (Mumbai edge, HTTP/2+3)
    │   ├── iam.tf                      ← Least-privilege IAM roles + policies
    │   ├── iam_devops.tf               ← IAM roles for CodePipeline, CodeBuild, CodeDeploy
    │   ├── bedrock.tf                  ← Bedrock Agent creation + alias
    │   ├── cloudwatch.tf               ← Log groups + dashboards
    │   ├── codebuild.tf                ← 4 CodeBuild projects + SSM parameters
    │   ├── codepipeline.tf             ← 2 pipelines, CodeStar connection, SNS, artifact S3
    │   ├── codedeploy.tf               ← CodeDeploy app, deployment groups, Lambda aliases, alarms
    │   ├── outputs.tf                  ← Deployed resource URLs
    │   ├── terraform.tfvars            ← Account ID, region (gitignored)
    │   └── terraform.lock.hcl          ← Provider version lock
    ├── buildspec/
    │   ├── buildspec-layers.yml        ← CodeBuild: build Lambda layers + zip handlers
    │   ├── buildspec-terraform-plan.yml← CodeBuild: terraform plan
    │   ├── buildspec-terraform-apply.yml← CodeBuild: terraform apply + CodeDeploy trigger
    │   └── buildspec-frontend.yml      ← CodeBuild: S3 sync + CloudFront invalidation
    ├── appspec/
    │   ├── appspec-stocks-signal.yml   ← CodeDeploy AppSpec template for stocks-signal
    │   └── appspec-options-analysis.yml← CodeDeploy AppSpec template for options-analysis
    └── layers/
        ├── build_layers.sh             ← Script to create Lambda layer ZIPs
        └── zips/
            ├── trading-backend-layer.zip   ← backend/ agents + utils (~500 KB)
            ├── trading-heavy-layer.zip     ← pandas, numpy, scipy, ta, yfinance (~400 MB)
            ├── trading-nlp-layer.zip       ← VADER, feedparser, beautifulsoup4 (~20 MB)
            └── trading-export-layer.zip    ← openpyxl (~5 MB)
```

---

## 💰 Cost Breakdown

**Monthly cost @ moderate usage (single active user):**

| AWS Service | Free Tier Allowance | My Usage | Monthly Cost |
|-------------|-------------------|----------|-------------|
| **Lambda** | 400K GB-sec + 1M requests | ~1.4M GB-sec | **~$17** |
| **DynamoDB** | 25 RCU/WCU always-free | ~10 RCU/WCU | **₹0** |
| **API Gateway** | 1M requests/month | ~200K requests | **₹0** |
| **CloudFront** | 1 TB data transfer | ~5 GB | **₹0** |
| **S3** | 5 GB storage | ~100 MB | **₹0** |
| **EventBridge** | 14M invocations/month | ~10K invocations | **₹0** |
| **CloudWatch** | 5 GB logs/month | ~2 GB | **₹0** |
| **Bedrock AI** | — | ~2–5M tokens | **₹150–400** |
| **CodePipeline** | 1 free pipeline/month | 2 pipelines | **~$1** |
| **CodeBuild** | 100 min free/month | ~10 deploys/month | **~$1.35** |
| **CodeDeploy (Lambda)** | Always free | — | **₹0** |
| **X-Ray** | 100K traces free/month | ~50K traces | **₹0** |
| | | **TOTAL** | **~$19–25/month (~₹1,600–2,100)** |

> **Why Lambda exceeds free tier:** The 60-second market-hours refresh (9:15–3:30 IST) creates ~375 refresh cycles/day during trading hours. Each cycle hits the stock signal Lambda (1 GB RAM, ~20s × 4 pages), pushing monthly GB-seconds to ~1.4M — above the 400K free tier limit.

**Cost optimisations built in:**
- **Tab-visibility guard** — refresh pauses when the browser tab is hidden/minimised, saving ~50–60% of compute on typical usage
- **`trading_market_status` Lambda** rewritten to use `urllib.request` (stdlib) instead of yfinance — cut duration from ~10s to ~1s and memory from 512 MB to 256 MB (~90% cheaper per call)
- After market hours (17.75h/day): refresh drops to 5 minutes → 213 cycles vs 375 — no extra cost outside trading hours

**Bedrock AI cost detail:**
- Claude Haiku 3.5: ~$0.25/1M input tokens, ~$1.25/1M output tokens (signal validation + chat)
- Nova Micro: ~$0.035/1M input tokens (headline classification only)

**Comparison:** Zerodha Streak (₹500/mo) | Chartink Pro (₹1500/mo) | TradingView (₹1000/mo) — none include AI chat, intraday ORB signals, or options Greeks.

---

## 🔒 Security

- **Cognito authentication** — every page and API route requires a valid JWT. Unauthenticated requests to `/api/*` return `401`
- **Per-user data isolation** — wishlist and portfolio use the Cognito `sub` (UUID) as the DynamoDB partition key, not a shared ID
- **JWT auto-refresh** — Cognito refresh tokens (30-day) silently renew access tokens; users stay logged in without re-entering credentials
- **CloudFront-only** entry point (S3 bucket private, Origin Access Identity)
- **IAM least-privilege** — each Lambda gets only the permissions it needs
- **DynamoDB**: Lambda-only access (no public endpoints)
- **Pre-signed URLs** for Excel export (1-hour expiry, then auto-invalidated)
- **No hardcoded credentials** — terraform.tfvars gitignored, no .env in repo
- **Terraform state** encrypted
- **PITR enabled** on wishlist + portfolio tables (point-in-time recovery)
- **CORS** restricted to CloudFront origin domain

---

## 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI dev server with hot-reload
python run.py
# Opens http://localhost:8000 with full dashboard

# Or manually:
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

**Requirements:** Python 3.12+, pip, internet connection (for yfinance + RSS feeds)

---

## 🚀 Deployment (AWS)

### Option A: AWS-Native Pipeline (Recommended — v3.0)

Deployments are now fully automated via **AWS CodePipeline**. Just push to `main`:

```bash
git push origin main
```

**What happens automatically:**
1. CodePipeline detects the push via CodeStar GitHub connection
2. CodeBuild builds Lambda layers + zips all handlers
3. CodeBuild runs `terraform plan`
4. **You get an email** — review the plan and approve/reject
5. CodeBuild runs `terraform apply`
6. CodeDeploy shifts traffic to new Lambda versions (canary for stocks-signal, linear for options-analysis)

**One-time setup (first deployment only):**
```bash
# 1. Set your Terraform state bucket in SSM
aws ssm put-parameter --name "/trading/tf-state-bucket" --type "String" --value "YOUR_TF_STATE_BUCKET_NAME" --overwrite

# 2. Apply with local credentials to create the pipeline infrastructure
cd infrastructure/terraform
terraform init -backend-config="bucket=YOUR_TF_STATE_BUCKET" -backend-config="key=trading/terraform.tfstate" -backend-config="region=us-east-1"
terraform plan -var="aws_account_id=$(aws sts get-caller-identity --query Account --output text)" -var="lambda_layers_built=true" -out=tfplan.tmp
terraform apply tfplan.tmp

# 3. Activate the GitHub connection in AWS console (30 seconds)
# Go to: https://us-east-1.console.aws.amazon.com/codesuite/settings/connections
# Find "trading-github-connection" → click "Update pending connection" → authorize GitHub App

# 4. Confirm the SNS approval email
# Check singh.arya1097@gmail.com for "AWS Notification - Subscription Confirmation" → click the link
```

**Monitor pipelines:**
```
https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/trading-infra-pipeline/view
https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/trading-frontend-pipeline/view
```

---

### Option B: Manual Terraform Deploy (Break-glass / Local)

```bash
# 1. Build Lambda layers
cd infrastructure/layers
bash build_layers.sh

# 2. Configure Terraform
cd ../terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your AWS account ID

# 3. Deploy infrastructure
terraform init
terraform plan
terraform apply

# 4. Copy Cognito IDs into app.js (lines 11-12)
terraform output cognito_user_pool_id   # → COGNITO_USER_POOL_ID in app.js
terraform output cognito_client_id      # → COGNITO_CLIENT_ID in app.js

# 5. Upload frontend to S3
BUCKET=$(terraform output -raw frontend_bucket)
DIST=$(terraform output -raw cloudfront_distribution_id)

aws s3 sync ../../frontend/ s3://$BUCKET/ --delete \
  --cache-control "public,max-age=31536000,immutable" --exclude "index.html"
aws s3 cp ../../frontend/index.html s3://$BUCKET/index.html \
  --cache-control "no-cache,no-store,must-revalidate"

# 6. Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $DIST --paths "/*"
```

---

## 🗺️ Roadmap

### 🎯 Next Sprint (High ROI)
- 📱 **PWA** — Install on phone like a native app
- 🔐 **Telegram Bot** — `/signal TCS` → full analysis; instant alerts on new STRONG signals
- 🧪 **Full Backtesting Engine** — 1-year replay of any strategy; win rate + Sharpe ratio + max drawdown
- 🧠 **Fine-tuned Sentiment** — Custom model trained on Indian financial news
- 📊 **Automated Trailing Stops** — DynamoDB auto-updates stop-loss to breakeven at 50% profit
- 🌐 **Expandable Universe** — Let users add custom watchlists beyond 80 stocks

### 🚀 Recently Shipped (v2.0 — 15 Critical Improvements)

#### Core Stability & Reliability
- ✅ **RSS Feed Timeout Protection** — 5s timeout on feedparser to prevent Lambda crashes from stuck feeds
- ✅ **NIFTY Column Guard** — Validation check prevents silent RS ratio failures if yfinance schema changes

#### User Experience & Alerts
- ✅ **Browser Push Notifications** — Real-time popup when wishlist stocks flip to STRONG BUY/SELL
- ✅ **Signal Performance Tracker** — localStorage tracking + accuracy badge showing hit rate % per signal type
- ✅ **ORB Session Caching** — Opening Range Breakout values persist across refreshes via localStorage with date matching

#### Data & Analysis
- ✅ **5-Minute Intraday Support** — Parallel yfinance fetch for 5m bars; switch 5m ↔ 15m on chart modal
- ✅ **FII/DII Market Data** — New `/api/fii-dii` Lambda; market bias badge (BEARISH/BULLISH) with ±5 to ±8 score adjustments
- ✅ **Fibonacci Retracements** — 23.6%, 38.2%, 50%, 61.8% levels from 52W high/low shown in modal stats
- ✅ **Volume Profile Histogram** — Horizontal bar chart with POC (Point-of-Control) highlighting institutional levels
- ✅ **IV Percentile Bootstrap Fallback** — Removed 5-day minimum; returns early estimate with "2/5 days" label

#### Validation & Risk Management
- ✅ **Multi-Timeframe Trend Confirmation** — Daily trend filter prevents STRONG BUY in downtrends; daily bullish adds +5 bonus
- ✅ **Liquidity & Slippage Warning** — Stocks < 30% of avg volume get -5 score reduction; prevents thin-stock surprises
- ✅ **Portfolio Sector Concentration** — Red warning if any sector ≥40% of holdings; prevents correlated drawdowns
- ✅ **Trailing Stop Badge** — "🔒 Raise stop to breakeven" reminder when profit ≥10%
- ✅ **Custom Stock Analysis** — Search bar analyzes ANY NSE/BSE symbol on-demand (not limited to 80-stock list)

#### Previous Releases
- ✅ **Refresh Architecture** — Stale-while-revalidate + merge-in-place: all 80 cards stay on screen during refresh
- ✅ **Sort Bar** — Sort grid by Score / R:R ratio / Change% / Volume with one click
- ✅ **Signal Changed Badge** — ↑ UPGRADED / ↓ DOWNGRADED badge on cards that changed since last refresh
- ✅ **Live Data** — Removed 15-min DynamoDB cache; all signals computed fresh on every request
- ✅ **Cognito Authentication** — Per-user wishlist and portfolio isolation
- ✅ **CI/CD Pipeline** — GitHub Actions auto-deploys infrastructure and frontend

### v3.0 — AWS-Native DevOps Pipeline
- ✅ **AWS CodePipeline** — Replaced GitHub Actions with 2 fully managed pipelines (infra + frontend)
- ✅ **AWS CodeBuild** — 4 build projects: layer build, terraform plan, terraform apply, frontend deploy
- ✅ **AWS CodeDeploy** — Canary + linear traffic shifting for Lambda with auto-rollback on errors
- ✅ **Lambda Aliases** — `:live` alias on stocks-signal and options-analysis; API Gateway routes to alias
- ✅ **CodeStar Connection** — Secure GitHub OAuth integration (no PATs, no secrets to rotate)
- ✅ **Manual Approval Gate** — SNS email notification before every terraform apply
- ✅ **Auto-Rollback** — CloudWatch alarms on Lambda error metrics trigger instant CodeDeploy rollback
- ✅ **AWS X-Ray** — Distributed tracing enabled on all 14 Lambda functions
- ✅ **SSM Parameter Store** — Secrets (bucket names, distribution IDs) injected into CodeBuild at runtime
