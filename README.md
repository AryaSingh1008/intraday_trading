# 📈 AI-Powered Intraday Trading Assistant

**Real-time NSE/BSE stock analysis with institutional-grade AI signals.**

A fully serverless cloud platform combining technical analysis, news sentiment, and AI-powered recommendations. Deployed on AWS with 100% uptime, zero infrastructure overhead, and pay-as-you-go pricing (~$2–5/month).

🔗 **Live Demo:** [https://dax4jpe1e1lnf.cloudfront.net](https://dax4jpe1e1lnf.cloudfront.net)

---

## 🎯 Why I Built This

My dad has been trading for years, but the process always frustrated me to watch. He'd have five browser tabs open on his phone — one for charts, one for news, one for a screener — switching between them constantly, trying to piece together a picture before the opportunity slipped away.

I built this so he has **one place to look**. Open the dashboard, see every stock's signal, read the news sentiment, and ask the AI a question — all without leaving the page. No subscriptions, no delays, no tab chaos.

> This project is in **alpha** and actively evolving based on real trading feedback. Features and signals will improve over time.

### What Makes It Different

| Feature | Typical Trading Tools | This Platform |
|---------|----------------------|---------------|
| **Cost** | ₹500–2000/month | ~$2–8/month (AWS free tier + Bedrock AI) |
| **AI Chat** | None or basic | Ask anything in plain English, Claude Haiku 3.5 provides institutional analysis |
| **Signal Engine** | 2–3 indicators | 12 indicators + VWAP + support/resistance + 200-day SMA + AI-validated + news sentiment (adaptive weighting) |
| **Data Source** | Paid APIs | 100% free (yfinance, NSE, Google News RSS, Bedrock AI) |
| **Infrastructure** | Always-on servers | Serverless — scales to $0 when market is closed |
| **Export** | Screenshot or manual | One-click Excel export of all 80 stocks |

---

## ✨ Key Features

### 📊 Smart Stock Signals
- **80 Indian stocks** across all sectors scored using 12 technical indicators (RSI, MACD, Bollinger, EMA 9/21, SMA 20/50/200, Golden/Death Cross, ADX, Stochastic, Volume, RSI Divergence, VWAP, Support/Resistance) + sentiment from 6 news sources + AI validation
- Uses **1 year of daily data** from yfinance — enough for 200-day moving averages and reliable long-term trend detection
- AI Signal Validator (Claude Haiku) reviews every signal, catches contradictions, flags risks
- AI Headline Classifier (Nova Micro) upgrades impactful news sentiment automatically
- Adaptive weighting adjusts technical vs sentiment ratio based on news volume
- Signals: **STRONG BUY / BUY / HOLD / SELL / STRONG SELL** with confidence scores + AI thesis

### ⚡ Progressive Loading with Pagination
- First 20 stocks load instantly (~3s), remaining stocks load in background
- Paginated view (20 stocks per page) with smooth navigation
- No more waiting for all 80 stocks — browse page 1 while pages 2–4 load behind the scenes

### 🤖 AI Chat (Claude Haiku 3.5 via Bedrock)
- Ask in plain English: *"Should I buy RELIANCE today?"* or *"Compare TCS vs INFY"*
- AI calls the same signal engine you see on the dashboard — real analysis, not generic answers
- Powered by Claude Haiku 3.5 with tool-use for live technical analysis, news sentiment, and options data
- Multi-step reasoning: analyzes 12 indicators + news + relative strength before answering

### 💼 Portfolio Tracker
- Add holdings with buy price and quantity
- Live P&L calculation (day gain + total gain) using real-time prices
- Search and add any of the 43 tracked stocks via autocomplete

### 📰 Market News with Sentiment
- Aggregates news from 6 RSS feeds (Economic Times, Moneycontrol, LiveMint, etc.)
- Each headline tagged **Bullish / Bearish / Neutral** using VADER NLP + finance lexicon
- Recency-weighted: fresh news impacts signals more than old news

### ⭐ Wishlist & Excel Export
- Bookmark stocks to a persistent watchlist (saved in DynamoDB)
- One-click Excel export with full analysis for all 80 stocks

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
User asks AI → Bedrock calls signal engine tools → returns analysis
```

**EventBridge** runs a warmup every 5 minutes during market hours, pre-caching stock data so most user requests hit cache and return in < 1 second.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    AWS SERVERLESS STACK                        │
└────────────────────────────────────────────────────────────────┘

  👤 Browser (Chrome/Mobile)
         │
         ↓ HTTPS
  ┌──────────────────┐
  │ CloudFront CDN   │  (Global edge network, HTTP/2 + HTTP/3)
  └────┬──────┬──────┘
       │      │
  Static │     │ API calls
  files  │     │ /api/*
    ↓    │     ↓
  ┌────┐ │  ┌──────────────────┐
  │ S3 │ │  │ API Gateway      │
  │SPA │ │  │ (15 routes)      │
  └────┘ │  └────────┬─────────┘
         │           │
         │           ↓
         │      ┌─────────────┐
         │      │13 Lambdas:  │
         │      │• stocks     │
         │      │• options    │
         │      │• news       │
         │      │• portfolio  │
         │      │• bedrock    │
         │      │  (AI chat)  │
         │      └──┬──┬──┬────┘
         │         │  │  │
  ┌──────┼─────────┘  │  │
  │      │            │  │
  ↓      ↓            ↓  ↓
[DynamoDB] [Bedrock] [yfinance] [RSS feeds]
- cache      Haiku    prices      6 sources
- wishlist   3.5 +    NSE opts    + AI
- portfolio  Nova M.  sentiment   headlines
- iv-hist.
```

---

## 🛠️ Tech Stack

| Layer | Technology | Service |
|-------|-----------|---------|
| **Frontend** | HTML5 + Bootstrap 5 + Chart.js | S3 + CloudFront (Mumbai edge) |
| **Backend** | 13 Lambda functions (Python 3.12) | AWS Lambda |
| **Database** | NoSQL, serverless, auto-scale | DynamoDB |
| **AI** | Claude Haiku 3.5 (chat + signal validation) + Nova Micro (headline classification) | AWS Bedrock |
| **API** | HTTP v2, 15 routes, 29s timeout | API Gateway |
| **Data Sources** | yfinance, NSE, 6 RSS feeds | Free (no paid APIs) |
| **IaC** | 10+ Terraform modules | Terraform |
| **Caching** | DynamoDB with 15-min TTL | EventBridge warmup |

---

## 📊 Signal Algorithm

**12 Technical Indicators (1 year of daily data):**
```
RSI (±20) | MACD (±15) | Bollinger (±15) | EMA 9/21 (±15) | RSI Div (±12)
SMA 20/50/200 (±10) | Volume (±10) | ADX (±8) | Stochastic (±8)
VWAP | Support/Resistance (S1/R1 pivot points)
Golden Cross / Death Cross — 50-day SMA vs 200-day SMA
```

**AI Signal Validator (Claude Haiku 3.5):**
- Receives all 12 indicators + sentiment score + relative strength vs NIFTY 50
- Validates the BUY/SELL/HOLD signal, identifies contradictions, flags risks
- Returns: thesis, confidence level, risk warnings, conflicting signals

**Sentiment Analysis from 6 RSS feeds:**
- VADER NLP + 100+ finance domain lexicon terms
- AI Headline Classifier (Nova Micro): top 3 headlines reclassified for impact (HIGH/MEDIUM/LOW)
- High-impact news gets weight boost; sentiment automatically upgraded/downgraded by AI
- Recency weighting (fresh news > old)
- Score: -50 (bearish) to +50 (bullish)

**Final Score (Adaptive Weighting):**
```
Score = Technical × (75%|65%|55%) + Sentiment × (25%|35%|45%)

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
│
├── backend/                            ← Agents (used in Lambda + local)
│   ├── agents/
│   │   ├── technical_agent.py          ← 12 indicators + VWAP + support/resistance
│   │   ├── sentiment_agent.py          ← VADER + RSS + AI headline classifier (Nova Micro)
│   │   ├── signal_agent.py             ← Orchestrator (combines tech + sentiment + RS ratio)
│   │   └── options_agent.py            ← NSE analysis
│   ├── data/
│   │   ├── stock_fetcher.py            ← yfinance (batch + single)
│   │   ├── options_fetcher.py          ← NSE chain
│   │   └── playwright_fetcher.py       ← Browser
│   ├── utils/
│   │   ├── excel_exporter.py
│   │   ├── greeks.py
│   │   ├── iv_history_store.py
│   │   └── wishlist_store.py
│   └── app.py                          ← FastAPI (local dev)
│
├── frontend/                           ← SPA (S3 + CloudFront)
│   ├── index.html                      ← 4 tabs + pagination
│   ├── css/style.css
│   └── js/app.js                       ← Progressive loading + pagination
│
├── lambdas/                            ← AWS Lambda handlers
│   ├── trading_stocks_signal/          ← Main engine (paginated + AI validator)
│   │   ├── handler.py                  ← Calls signal_agent + ai_validator
│   │   └── ai_validator.py             ← Claude Haiku signal validation
│   ├── trading_options_analysis/
│   ├── trading_news_sentiment/
│   ├── trading_wishlist/
│   ├── trading_portfolio/              ← Holdings tracker
│   ├── trading_market_status/
│   ├── trading_excel_export/
│   ├── trading_cache_clear/
│   ├── trading_bedrock_chat/           ← AI chat (Haiku 3.5)
│   ├── trading_bedrock_technical_tool/
│   ├── trading_bedrock_sentiment_tool/
│   └── trading_bedrock_options_tool/
│
└── infrastructure/                     ← Terraform IaC
    ├── terraform/
    │   ├── api_gateway.tf
    │   ├── bedrock.tf
    │   ├── cloudfront.tf
    │   ├── dynamodb.tf
    │   ├── eventbridge.tf
    │   ├── iam.tf
    │   ├── lambda_functions.tf
    │   ├── lambda_layers.tf
    │   ├── s3.tf
    │   ├── terraform.tfvars            ← AWS account ID, region
    │   ├── terraform.lock.hcl
    │   └── variables.tf
    └── layers/
        ├── trading-backend-layer.zip
        ├── trading-heavy-layer.zip     ← pandas, numpy, ta
        ├── trading-nlp-layer.zip       ← VADER, feedparser
        └── trading-export-layer.zip    ← openpyxl
```

---

**Cost:** $2–8/month @ moderate usage
- Lambda: 1M calls/month FREE
- DynamoDB: 25 RCU/WCU FREE
- CloudFront: 1 TB/month FREE (Mumbai edge)
- S3: 5 GB FREE
- API Gateway: 1M calls/month FREE
- Bedrock AI: ~$2–5/month (signal validator + chatbot + headline classifier)
  - Claude Haiku 3.5: ~$0.06 per 1M input tokens, ~$0.24 per 1M output tokens
  - Nova Micro: ~$0.035 per 1M input tokens (headline classification only)

---

## 🔒 Security

- CloudFront-only entry point (S3 bucket private)
- IAM roles with least-privilege per Lambda
- DynamoDB: Lambda-only access (no public endpoints)
- Pre-signed URLs for Excel export (1-hour expiry)
- No hardcoded credentials (terraform.tfvars gitignored)
- Terraform state encrypted

---

## 🔧 Local Development

```bash
pip install -r requirements.txt
python run.py
# Opens http://localhost:8000
```
