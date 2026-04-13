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
| **Signal Engine** | 2–3 indicators | 13 indicators + VWAP + ORB + support/resistance + 200-day SMA + AI-validated + news sentiment (adaptive weighting) |
| **News Sentiment** | Separate tab / manual reading | Built into signal score — 6 RSS feeds auto-weighted by recency (intraday-tightened) + source authority |
| **Data Source** | Paid APIs | 100% free (yfinance, NSE, Google News RSS, Bedrock AI) |
| **Infrastructure** | Always-on servers | Serverless — scales to $0 when market is closed |
| **Index Strip** | Separate terminal / app | NIFTY 50, BANKNIFTY, India VIX live in the header — always visible |
| **R:R Ratio** | Manual calculation | Auto-calculated on every signal card from ATR-based targets |
| **Options Analysis** | Separate platform | PCR, IV percentile, Greeks, max-pain — all in-dashboard |
| **Export** | Screenshot or manual | One-click Excel export of all 80 stocks |
| **Mobile** | Desktop-first | Mobile-responsive — built for trading from a phone |

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
Yahoo Finance (1yr daily + 1d intraday 15m bars)
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

### Lambda Functions (13 Total)

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
| News Headlines | 6 RSS Feeds (ET, MC, BS, LM, Yahoo, Google) | Every 2–5 min | Weighted by source authority |
| Options Chain | NSE Public API (curl_cffi TLS fingerprint) | Real-time | Fallback: Yahoo Finance → Synthetic chain |
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

### AI Signal Validator (Claude Haiku 3.5)
- Receives all 12 indicators + sentiment score + relative strength vs NIFTY 50
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
    │   ├── bedrock.tf                  ← Bedrock Agent creation + alias
    │   ├── cloudwatch.tf               ← Log groups + dashboards
    │   ├── outputs.tf                  ← Deployed resource URLs
    │   ├── terraform.tfvars            ← Account ID, region (gitignored)
    │   └── terraform.lock.hcl          ← Provider version lock
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
| | | **TOTAL** | **~$17–22/month (~₹1,400–1,800)** |

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

```bash
# 1. Build Lambda layers
cd infrastructure/layers
bash build_layers.sh

# 2. Configure Terraform
cd ../terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your AWS account ID

# 3. Deploy infrastructure (creates Cognito User Pool + JWT authorizer)
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

> **First-time Cognito deploy:** If your CI/CD role (`github-actions-trading`) was created before Cognito was added, you need to grant it Cognito permissions once manually before Terraform can run:
> ```bash
> aws iam put-role-policy \
>   --role-name github-actions-trading \
>   --policy-name trading-cognito-access \
>   --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["cognito-idp:*"],"Resource":"*"}]}'
> ```
> After the first `terraform apply`, Terraform manages this policy automatically.

---

## 🗺️ Roadmap

- 🔔 **Push Notifications** — Alert when a watchlist stock flips to STRONG BUY/SELL
- 📱 **PWA** — Install on phone like a native app
- 🧪 **Backtesting Engine** — "Would this signal have worked 6 months ago?"
- 🧠 **Fine-tuned Sentiment** — Custom model trained on Indian financial news
- 📊 **Performance Dashboard** — Signal accuracy tracking over time

**Recently Shipped:**
- ✅ **Refresh Architecture** — Stale-while-revalidate + merge-in-place: all 80 cards stay on screen during every refresh; background refresh guard covers all 4 pages to prevent overlap; single DOM render pass per cycle (was 4×)
- ✅ **Sector Filter Fix** — Default signal filter changed to "All"; clicking a sector auto-resets the signal filter so Banking/Finance/etc. always show stocks regardless of market conditions
- ✅ **Sort Bar** — Sort grid by Score / R:R ratio / Change% / Volume with one click
- ✅ **Compact Signal Pill Bar** — 5-signal summary compressed into a single interactive row above the grid; each pill filters the view on click
- ✅ **ORB + Day High/Low** — Opening Range Breakout detection on cards with intraday high/low from 15-min bars
- ✅ **Signal Changed Badge** — ↑ UPGRADED / ↓ DOWNGRADED badge on cards that changed signal since the last refresh (localStorage snapshot, no extra API call)
- ✅ **Live Data** — Removed 15-min DynamoDB cache; all signals now computed fresh on every request so buy/sell targets always match current price
- ✅ **Cognito Authentication** — Email/password login with per-user wishlist and portfolio isolation
- ✅ **CI/CD Pipeline** — GitHub Actions deploys infrastructure and frontend on push to `main`
