# 📈 AI-Powered Intraday Trading Assistant

**Real-time NSE/BSE stock analysis with institutional-grade AI signals.**

A fully serverless cloud platform combining technical analysis, news sentiment, and AI-powered recommendations. Deployed on AWS with 100% uptime, zero infrastructure overhead, and pay-as-you-go pricing (~$2–5/month).

🔗 **Live Demo:** [https://dax4jpe1e1lnf.cloudfront.net](https://dax4jpe1e1lnf.cloudfront.net)

---

## 🎯 Why I Built This

My dad is an active trader, and I watched him struggle daily — juggling multiple apps and browser tabs on his phone, switching between charts, news, and screeners just to analyze a handful of stocks. By the time he'd pieced together a view, the moment had often passed.

I wanted to build him a **single dashboard** where he could see signals, news sentiment, and AI-powered analysis for all his stocks in one place — no tab-switching, no paid subscriptions, no delays. This is that tool.

> This project is currently in **alpha**. It's functional and actively used, but will continue to evolve based on real trading feedback and needs.

### What Makes It Different

| Feature | Typical Trading Tools | This Platform |
|---------|----------------------|---------------|
| **Cost** | ₹500–2000/month | ~$2–5/month (AWS free tier) |
| **AI Chat** | None or basic | Ask anything in plain English, get institutional analysis |
| **Signal Engine** | 2–3 indicators | 10 technical indicators + news sentiment (adaptive weighting) |
| **Data Source** | Paid APIs | 100% free (yfinance, NSE, Google News RSS) |
| **Infrastructure** | Always-on servers | Serverless — scales to $0 when market is closed |
| **Export** | Screenshot or manual | One-click Excel export of all 43 stocks |

---

## ✨ Key Features

### 📊 Smart Stock Signals
- **43 NIFTY 50 stocks** scored using 10 technical indicators (RSI, MACD, Bollinger, EMA, SMA, ADX, Stochastic, Volume, RSI Divergence) + sentiment from 6 news sources
- Adaptive weighting adjusts technical vs sentiment ratio based on news volume
- Signals: **STRONG BUY / BUY / HOLD / SELL / STRONG SELL** with confidence scores

### ⚡ Progressive Loading with Pagination
- First 10 stocks load instantly (~3s), remaining stocks load in background
- Paginated view (10 stocks per page) with smooth navigation
- No more waiting for all 43 stocks — browse page 1 while pages 2–5 load behind the scenes

### 🤖 AI Chat (Amazon Bedrock)
- Ask in plain English: *"Should I buy RELIANCE today?"* or *"Compare TCS vs INFY"*
- AI calls the same signal engine you see on the dashboard — real analysis, not generic answers
- Powered by Amazon Nova Lite with tool-use for live data access

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
- One-click Excel export with full analysis for all 43 stocks

---

## 🔄 How It Works

```
User opens website
      │
      ↓
CloudFront serves static files from nearest edge (< 50ms)
      │
      ↓
Frontend requests first 10 stocks → API Gateway → Lambda
      │                                              │
      │                                    Checks DynamoDB cache
      │                                    (15-min TTL)
      │                                              │
      │                              Cache HIT → return instantly
      │                              Cache MISS → batch fetch from yfinance
      │                                              │
      │                                    Run 10 technical indicators
      │                                    + sentiment analysis
      │                                              │
      │                                    Cache results in DynamoDB
      │                                              │
      ↓                                              ↓
Page 1 renders immediately          Background: fetch remaining stocks
      │                              (pages 2–5 load silently)
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
- cache      Nova     prices      6 sources
- wishlist   Lite     NSE opts    sentiment
- portfolio
- iv-hist.
```

---

## 🛠️ Tech Stack

| Layer | Technology | Service |
|-------|-----------|---------|
| **Frontend** | HTML5 + Bootstrap 5 + Chart.js | S3 + CloudFront |
| **Backend** | 13 Lambda functions (Python 3.12) | AWS Lambda |
| **Database** | NoSQL, serverless, auto-scale | DynamoDB |
| **AI/Chat** | Amazon Nova Lite (tool-use) | AWS Bedrock |
| **API** | HTTP v2, 15 routes, 29s timeout | API Gateway |
| **Data Sources** | yfinance, NSE, 6 RSS feeds | Free (no paid APIs) |
| **IaC** | 10+ Terraform modules | Terraform |
| **Caching** | DynamoDB with 15-min TTL | EventBridge warmup |

---

## 📊 Signal Algorithm

**10 Technical Indicators:**
```
RSI (±20) | MACD (±15) | Bollinger (±15) | EMA (±15) | RSI Div (±12)
SMA (±10) | Volume (±10) | ADX (±8) | Stochastic (±8)
```

**Sentiment Analysis from 6 RSS feeds:**
- VADER NLP + finance domain lexicon
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
│   │   ├── technical_agent.py          ← 10 indicators
│   │   ├── sentiment_agent.py          ← VADER + RSS
│   │   ├── signal_agent.py             ← Orchestrator
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
│   ├── trading_stocks_signal/          ← Main engine (paginated + batch)
│   ├── trading_options_analysis/
│   ├── trading_news_sentiment/
│   ├── trading_wishlist/
│   ├── trading_portfolio/              ← Holdings tracker
│   ├── trading_market_status/
│   ├── trading_excel_export/
│   ├── trading_cache_clear/
│   ├── trading_bedrock_chat/           ← AI chat
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

## 🚀 Deployment

**Deploy to AWS:**
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

**Cost:** $2–5/month @ moderate usage
- Lambda: 1M calls/month FREE
- DynamoDB: 25 RCU/WCU FREE
- CloudFront: 1 TB/month FREE
- S3: 5 GB FREE
- API Gateway: 1M calls/month FREE
- Bedrock: Pay per token

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
