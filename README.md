# 📈 AI-Powered Intraday Trading Assistant

**Real-time NSE/BSE stock analysis with institutional-grade AI signals.**

A fully serverless cloud platform combining technical analysis, news sentiment, and AI-powered recommendations. Deployed on AWS with 100% uptime, zero infrastructure overhead, and pay-as-you-go pricing (~$2–8/month).

🔗 **Live Demo:** [https://dax4jpe1e1lnf.cloudfront.net](https://dax4jpe1e1lnf.cloudfront.net)

---

## 🎯 Why I Built This

My dad has been trading for years, but the process always frustrated me to watch. He'd have five browser tabs open on his phone — one for charts, one for news, one for a screener — switching between them constantly, trying to piece together a picture before the opportunity slipped away.

I built this so he has **one place to look**. Open the dashboard, see every stock's signal, read the news sentiment, and ask the AI a question — all without leaving the page. No subscriptions, no delays, no tab chaos.

> *A junior research analyst that works 24/7, costs ₹200/month, and never takes a lunch break.*

> This project is in **alpha** and actively evolving based on real trading feedback. Features and signals will improve over time.

### What Makes It Different

| Feature | Typical Trading Tools | This Platform |
|---------|----------------------|---------------|
| **Cost** | ₹500–2000/month | ~$2–8/month (AWS free tier + Bedrock AI) |
| **AI Chat** | None or basic | Ask anything in plain English, Claude Haiku 3.5 provides institutional analysis |
| **Signal Engine** | 2–3 indicators | 12 indicators + VWAP + support/resistance + 200-day SMA + AI-validated + news sentiment (adaptive weighting) |
| **News Sentiment** | Separate tab / manual reading | Built into signal score — 6 RSS feeds auto-weighted by recency + source authority |
| **Data Source** | Paid APIs | 100% free (yfinance, NSE, Google News RSS, Bedrock AI) |
| **Infrastructure** | Always-on servers | Serverless — scales to $0 when market is closed |
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
- **Recency weighting**: 6h → 1.0, 24h → 0.85, 72h → 0.45, older → 0.30
- AI Headline Classifier (Nova Micro) reclassifies top 3 headlines for impact (HIGH/MEDIUM/LOW)

### ⭐ Wishlist & Excel Export
- Bookmark stocks to a persistent watchlist (saved in DynamoDB with PITR backup)
- One-click Excel export with full analysis for all 80 stocks
- Styled XLSX: signal-based background colors, formatted headers, title + disclaimer

### 🕐 Market Status & Auto-Refresh
- IST market hours indicator (9:15 AM – 3:30 PM, weekdays)
- 15-minute auto-refresh countdown with progress bar
- EventBridge warmup pre-caches data — most requests return in **< 1 second**

---

## 🔄 How It Works

```
User opens website
      │
      ↓
CloudFront serves static files from nearest edge (< 50ms)
      │
      ↓
Frontend requests first 20 stocks → API Gateway → Lambda
      │                                              │
      │                                    Checks DynamoDB cache
      │                                    (15-min TTL)
      │                                              │
      │                              Cache HIT → return instantly
      │                              Cache MISS → batch fetch from yfinance
      │                                              │
      │                                    Run 12 technical indicators
      │                                    + sentiment analysis + AI validation
      │                                              │
      │                                    Cache results in DynamoDB
      │                                              │
      ↓                                              ↓
Page 1 renders immediately          Background: fetch remaining stocks
      │                              (pages 2–4 load silently)
      ↓
User browses, clicks stock → modal with intraday chart + full analysis
      │
      ↓
User asks AI → Bedrock Agent calls 3 tools → returns reasoned analysis
```

**EventBridge Schedules (3 automated jobs):**
- **Every 5 min** (market hours): Pre-cache all 80 stock signals → < 1s user response
- **Every 2 min**: Refresh options chain data (keeps cache hot)
- **Daily 3:40 PM IST**: Snapshot ATM IV for 30-day rolling percentile history

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
│                    API Gateway (HTTP v2)                           │
│              15 Routes │ 29s timeout │ CORS enabled               │
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
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │DynamoDB  │  │DynamoDB  │  │DynamoDB  │  │DynamoDB  │
  │Cache     │  │Wishlist  │  │Portfolio │  │IV History│
  │(15m TTL) │  │(PITR)    │  │(PITR)    │  │(31d TTL) │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │     External Data Sources (ALL FREE)                  │
  │  Yahoo Finance  │  NSE Public API  │  6 RSS Feeds    │
  │  (prices, OHLCV)│  (options chain) │  (news headlines)│
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
  │     EventBridge Scheduler (3 Automated Jobs)          │
  │  Every 5m : Warmup stock signals (market hours only) │
  │  Every 2m : Refresh options chain cache              │
  │  Daily 3:40PM : Snapshot IV for 30-day percentile    │
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
│  RSI (±20)  │ MACD (±15)      │ Bollinger (±15)       │
│  EMA 9/21 (±15) │ SMA 20/50 (±10) │ SMA 200 (±8)     │
│  Golden/Death Cross (±6/±12)  │ Volume z-score (±10)  │
│  ADX (±8)   │ Stochastic RSI (±8)  │ RSI Div (±12)   │
│  VWAP (±8)  │ Support/Resistance (±5)                 │
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
| `trading_options_refresh` | EventBridge warmup + IV history | 30s | backend, heavy |
| `trading_news_sentiment` | News aggregation endpoint | 20s | backend, nlp |
| `trading_wishlist` | Wishlist CRUD operations | 10s | backend |
| `trading_portfolio` | Holdings P&L tracker | 10s | backend |
| `trading_market_status` | IST market hours check | 5s | backend |
| `trading_excel_export` | XLSX generation + pre-signed S3 URL | 10s | backend, export |
| `trading_cache_clear` | Manual cache invalidation | 5s | backend |

### DynamoDB Tables (4)

| Table | PK | SK | TTL | Purpose |
|-------|----|----|-----|---------|
| `trading-cache` | `cache_key` | — | 15 min | Stock signals, options chains (auto-expires) |
| `trading-wishlist` | `user_id` | `symbol` | — | Persistent watchlist (PITR enabled) |
| `trading-portfolio` | `user_id` | `holding_id` | — | Holdings with buy price/qty (PITR enabled) |
| `trading-iv-history` | `symbol` | `date` | 31 days | 30-day rolling IV percentile snapshots |

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

---

## 🛠️ Tech Stack

| Layer | Technology | Why This Choice |
|-------|-----------|-----------------|
| **Frontend** | HTML5 + Bootstrap 5 + Chart.js (vanilla JS) | No framework overhead — loads in <3s on mobile, zero build step |
| **Backend** | 13 Lambda functions (Python 3.12) | Serverless — ₹0 when market closed. Python for pandas/numpy/ta ecosystem |
| **Database** | DynamoDB (PAY_PER_REQUEST) | Zero admin, free tier (25 RCU/WCU), auto-scales |
| **AI** | Claude Haiku 3.5 + Nova Micro (Bedrock) | Haiku: fast (1-2s), cheap ($0.25/1M tokens). Nova: headlines only ($0.035/1M) |
| **API** | API Gateway HTTP v2 (15 routes) | Low latency, 29s timeout, native Lambda integration |
| **CDN** | CloudFront (Mumbai edge) | HTTP/2+3, caching, S3 origin access identity |
| **Data** | yfinance, NSE API, 6 RSS feeds | 100% free — no paid APIs |
| **IaC** | Terraform (10+ modules) | Reproducible, state management, multi-resource orchestration |
| **Caching** | DynamoDB (15-min TTL) + EventBridge warmup | Pre-cached responses → <1s latency during market hours |
| **Scheduling** | EventBridge Scheduler (3 jobs) | Market-hours-only warmup → zero cost overnight |
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
| **Golden/Death Cross** | 50 vs 200 | ±6/±12 | Volume-confirmed 50-day vs 200-day crossover |
| **Support/Resistance** | Pivot points | ±5 | Price near S1/R1 — bounce/rejection zones |
| **Relative Strength** | vs NIFTY 50 | ±5 | RS >1.2 outperforming, <0.8 underperforming |

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
- Recency: 6h → 1.0, 24h → 0.85, 72h → 0.45, older → 0.30
- Source authority: ET/MC → 1.3x, BS/LM → 1.2x, others → 1.0x
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
    │   ├── api_gateway.tf              ← HTTP API v2 (15 routes, 29s timeout)
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

**Monthly cost @ moderate usage:**

| AWS Service | Free Tier Allowance | My Usage | Monthly Cost |
|-------------|-------------------|----------|-------------|
| **Lambda** | 1M requests/month | ~50K requests | **₹0** |
| **DynamoDB** | 25 RCU/WCU always-free | ~10 RCU/WCU | **₹0** |
| **API Gateway** | 1M requests/month | ~50K requests | **₹0** |
| **CloudFront** | 1 TB data transfer | ~5 GB | **₹0** |
| **S3** | 5 GB storage | ~100 MB | **₹0** |
| **EventBridge** | 14M invocations/month | ~10K invocations | **₹0** |
| **CloudWatch** | 5 GB logs/month | ~2 GB | **₹0** |
| **Bedrock AI** | — | ~2–5M tokens | **₹150–400** |
| | | **TOTAL** | **~₹200–600/month** |

**Bedrock AI cost detail:**
- Claude Haiku 3.5: ~$0.25/1M input tokens, ~$1.25/1M output tokens (signal validation + chat)
- Nova Micro: ~$0.035/1M input tokens (headline classification only)

**Comparison:** Zerodha Streak (₹500/mo) | Chartink Pro (₹1500/mo) | TradingView (₹1000/mo) — none include AI chat.

---

## 🔒 Security

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

# 3. Deploy
terraform init
terraform plan
terraform apply

# 4. Upload frontend to S3
aws s3 sync ../../frontend/ s3://<your-spa-bucket>/ --delete

# 5. Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

---

## 🗺️ Roadmap

- 🔔 **Push Notifications** — Alert when a watchlist stock flips to STRONG BUY/SELL
- 📱 **PWA** — Install on phone like a native app
- 🧪 **Backtesting Engine** — "Would this signal have worked 6 months ago?"
- 👥 **Multi-user Auth** — Cognito login for multiple family members
- 🔄 **CI/CD Pipeline** — GitHub Actions → auto-deploy on push
- 🧠 **Fine-tuned Sentiment** — Custom model trained on Indian financial news
- 📊 **Performance Dashboard** — Signal accuracy tracking over time
