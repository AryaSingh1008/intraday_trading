# 📈 AI Intraday Trading Assistant

A simplified, senior-friendly AI-powered stock analysis tool.
Built with **100% free tools** — no paid API keys required for basic use.

> ⚠️ **Disclaimer:** This tool is for **educational purposes only**.
> Trading involves risk and you may lose money.
> Always consult a financial advisor before investing real money.

---

## 🏗️ Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AI INTRADAY TRADING ASSISTANT                     │
│                      Complete Architecture                           │
└──────────────────────────────────────────────────────────────────────┘

         Your Dad's Browser (http://localhost:8000)
         ┌────────────────────────────────────────┐
         │           FRONTEND  (UI)               │
         │                                        │
         │  ┌─────────┐  ┌─────────┐  ┌───────┐  │
         │  │ Dashboard│  │ Stock   │  │ News  │  │
         │  │ Summary  │  │ Cards   │  │ Feed  │  │
         │  │ (counts) │  │BUY/SELL │  │Senti- │  │
         │  │          │  │  HOLD   │  │ment   │  │
         │  └─────────┘  └─────────┘  └───────┘  │
         │                                        │
         │  🟢 STRONG BUY   🟢 BUY                │
         │  🟡 HOLD         🔴 SELL               │
         │  🔴 STRONG SELL                         │
         │                                        │
         │  [Refresh]  [Export Excel]             │
         └─────────────────┬──────────────────────┘
                           │  HTTP / REST API
                           ▼
         ┌────────────────────────────────────────┐
         │         BACKEND  (FastAPI / Python)    │
         │                                        │
         │  REST Endpoints:                       │
         │  GET /api/stocks?market=IN             │
         │  GET /api/stock/{symbol}               │
         │  GET /api/news                         │
         │  GET /api/export  (→ Excel file)       │
         │  GET /api/market-status                │
         │                                        │
         │  ┌─────────────────────────────────┐  │
         │  │         AI AGENTS               │  │
         │  │                                 │  │
         │  │  ┌──────────────────────────┐   │  │
         │  │  │  1. Technical Agent      │   │  │
         │  │  │  ─────────────────────── │   │  │
         │  │  │  • RSI (14-period)       │   │  │
         │  │  │  • MACD (12,26,9)        │   │  │
         │  │  │  • Bollinger Bands (20)  │   │  │
         │  │  │  • SMA 20 & SMA 50       │   │  │
         │  │  │  • Volume Ratio          │   │  │
         │  │  │  Output: Score 0–100     │   │  │
         │  │  └──────────┬───────────────┘   │  │
         │  │             │ 70% weight         │  │
         │  │  ┌──────────▼───────────────┐   │  │
         │  │  │  2. Sentiment Agent      │   │  │
         │  │  │  ─────────────────────── │   │  │
         │  │  │  • Google News RSS Feed  │   │  │
         │  │  │  • Yahoo Finance RSS     │   │  │
         │  │  │  • VADER NLP (offline)   │   │  │
         │  │  │  Output: Score -50…+50   │   │  │
         │  │  └──────────┬───────────────┘   │  │
         │  │             │ 30% weight         │  │
         │  │  ┌──────────▼───────────────┐   │  │
         │  │  │  3. Signal Agent         │   │  │
         │  │  │  ─────────────────────── │   │  │
         │  │  │  Combines both scores:   │   │  │
         │  │  │  final = tech*0.7        │   │  │
         │  │  │        + sentiment*0.3   │   │  │
         │  │  │                          │   │  │
         │  │  │  > 70  → STRONG BUY 🟢🟢 │   │  │
         │  │  │  55-70 → BUY        🟢   │   │  │
         │  │  │  40-55 → HOLD       🟡   │   │  │
         │  │  │  25-40 → SELL       🔴   │   │  │
         │  │  │  < 25  → STRONG SELL🔴🔴 │   │  │
         │  │  └──────────────────────────┘   │  │
         │  └─────────────────────────────────┘  │
         │                                        │
         │  ┌─────────────────────────────────┐  │
         │  │       UTILITIES                 │  │
         │  │  • Excel Exporter (openpyxl)    │  │
         │  │  • 5-minute cache (in-memory)   │  │
         │  └─────────────────────────────────┘  │
         └─────────────────┬──────────────────────┘
                           │  HTTP (yfinance / feedparser)
                           ▼
         ┌────────────────────────────────────────┐
         │    FREE EXTERNAL DATA SOURCES          │
         │                                        │
         │  📊 Yahoo Finance  ──── yfinance lib   │
         │     (Real-time prices, OHLCV data)     │
         │     No API key needed!                 │
         │                                        │
         │  📰 Google News RSS ─── feedparser lib │
         │     (Latest headlines, no key needed)  │
         │                                        │
         │  🧠 VADER Sentiment ─── offline NLP    │
         │     (Runs 100% on your computer)       │
         └────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack (All FREE)

| Component | Technology | Why Free? |
|-----------|-----------|-----------|
| **Language** | Python 3.10+ | Open-source |
| **Backend** | FastAPI | Open-source |
| **Stock Data** | yfinance | Yahoo Finance (free) |
| **Technical Analysis** | pandas + numpy | Open-source |
| **AI/NLP Sentiment** | VADER | Free NLP library |
| **News** | Google News RSS | Free RSS feed |
| **Frontend** | HTML + Bootstrap 5 | Open-source CDN |
| **Charts** | Chart.js | Open-source CDN |
| **Excel Export** | openpyxl | Open-source |
| **Hosting (local)** | uvicorn | Open-source |

---

## 🤖 AI Agents Explained

### Agent 1: Technical Analysis Agent
Reads historical price data and calculates classic trading indicators:

| Indicator | What it does | Scoring |
|-----------|--------------|---------|
| **RSI** | Measures if stock is overbought or oversold | <30 = BUY, >70 = SELL |
| **MACD** | Shows momentum direction | Crossover up = BUY |
| **Bollinger Bands** | Shows if price is at extremes | Near lower = BUY |
| **SMA 20/50** | Trend direction | 20 > 50 = Uptrend |
| **Volume** | Confirms price moves | High volume + up = BUY |

### Agent 2: Sentiment Analysis Agent
Reads news headlines from free RSS feeds and scores them using VADER NLP:
- Positive news → Bullish signal
- Negative news → Bearish signal
- Mixed/neutral → No influence

### Agent 3: Signal Agent (Master)
Combines both agents with weighted scoring:
```
Final Score = Technical Score × 70% + Sentiment Score × 30%
```
Generates plain-English explanations so anyone can understand the signal.

---

## 📦 Free Datasets Available

| Dataset | Access Method | Coverage |
|---------|--------------|---------|
| **Yahoo Finance** | `yfinance` Python library | Global stocks, real-time |
| **NSE India** | `yfinance` with `.NS` suffix | All NSE-listed stocks |
| **BSE India** | `yfinance` with `.BO` suffix | All BSE-listed stocks |
| **Google News RSS** | `feedparser` | Real-time news headlines |
| **Yahoo Finance RSS** | `feedparser` | US stock news |

---

## 🚀 Installation & Setup

### Step 1: Install Python
Download Python 3.10 or newer from: https://www.python.org/downloads/

### Step 2: Open Terminal/Command Prompt
- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac**: Press `Cmd + Space`, type `Terminal`, press Enter

### Step 3: Navigate to Project Folder
```bash
cd /path/to/intraday_trading
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run the Application
```bash
python run.py
```

### Step 6: Open Browser
The browser will open automatically. If not, go to:
```
http://localhost:8000
```

---

## 📖 How to Use (For Dad)

### Understanding the Dashboard

**Traffic Light System:**
- 🟢🟢 **STRONG BUY** — AI strongly recommends buying this stock
- 🟢 **BUY** — Good signals to buy this stock
- 🟡 **HOLD** — Not clear, wait and watch
- 🔴 **SELL** — Signals suggest selling
- 🔴🔴 **STRONG SELL** — AI strongly recommends selling

**AI Score (0 to 100):**
- Above 65 = Good for buying
- 40 to 65 = Neutral, be careful
- Below 35 = Consider selling

**Risk Level:**
- 🟢 LOW — Stable stock, less risky
- 🟡 MEDIUM — Moderate risk
- 🔴 HIGH — Volatile stock, higher risk

### Step-by-Step Usage

1. **Open the app** → Browser opens automatically at http://localhost:8000
2. **Choose market** → Click "🇮🇳 Indian Stocks" or "🇺🇸 US Stocks"
3. **Look for green cards** → These are the BUY signals
4. **Click any stock card** → See detailed AI analysis
5. **Read the explanation** → Written in simple English
6. **Check the risk** → LOW risk is safer for conservative investors
7. **Export to Excel** → Click "Export Excel" to save a spreadsheet

### Important Rules
1. Never invest more than you can afford to lose
2. Always use stop-loss orders
3. Don't invest based on a single signal — look at the full picture
4. The market is unpredictable — even AI can be wrong!

---

## 📁 Project Structure

```
intraday_trading/
├── run.py                          ← START HERE (python run.py)
├── requirements.txt                ← Python dependencies
├── README.md                       ← This file
│
├── backend/
│   ├── app.py                      ← FastAPI server + API routes
│   ├── agents/
│   │   ├── technical_agent.py      ← RSI, MACD, Bollinger Bands
│   │   ├── sentiment_agent.py      ← News sentiment (VADER + RSS)
│   │   └── signal_agent.py         ← Master signal combiner
│   ├── data/
│   │   └── stock_fetcher.py        ← Yahoo Finance data fetcher
│   └── utils/
│       └── excel_exporter.py       ← Excel file creator
│
└── frontend/
    ├── index.html                  ← Main web page
    ├── css/
    │   └── style.css               ← Styling
    └── js/
        └── app.js                  ← Frontend logic
```

---

## ⚙️ Configuration

### Adding Custom Stocks
Open `backend/app.py` and find `INDIAN_STOCKS` or `US_STOCKS` dictionaries.
Add entries in the format:
```python
"SYMBOL.NS": "Company Name",    # For Indian NSE stocks
"SYMBOL.BO": "Company Name",    # For Indian BSE stocks
"SYMBOL":    "Company Name",    # For US stocks
```

### Common Indian Stock Symbols
| Symbol | Company |
|--------|---------|
| `RELIANCE.NS` | Reliance Industries |
| `TCS.NS` | Tata Consultancy Services |
| `INFY.NS` | Infosys |
| `HDFCBANK.NS` | HDFC Bank |
| `SBIN.NS` | State Bank of India |

### Common US Stock Symbols
| Symbol | Company |
|--------|---------|
| `AAPL` | Apple |
| `MSFT` | Microsoft |
| `GOOGL` | Alphabet/Google |
| `TSLA` | Tesla |
| `NVDA` | NVIDIA |

---

## 🔮 Future Improvements (Cloud Hosting)

When ready to move to cloud:

1. **Database**: Replace in-memory cache with **PostgreSQL** or **Redis**
2. **Model Upgrade**: Add **LSTM neural network** for price prediction
3. **Better Data**: Add **Alpha Vantage** or **Polygon.io** for tick data
4. **Hosting**: Deploy to **AWS / GCP / Azure** or **Render.com** (free tier)
5. **Alerts**: Add SMS/email alerts via Twilio/SendGrid
6. **Portfolio Tracker**: Track actual holdings and P&L
7. **Paper Trading**: Test strategies without real money
8. **Mobile App**: Convert to React Native for phone app

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No data" for a stock | Check internet connection; Yahoo Finance may be rate-limiting |
| App won't start | Run `pip install -r requirements.txt` again |
| Browser doesn't open | Manually go to http://localhost:8000 |
| Slow loading | First load takes 20-30s; subsequent loads use 5-min cache |
| Stock not found | Check symbol spelling; add `.NS` for Indian stocks |

---

## 📞 Support

For issues or feature requests, ask your son/daughter who set this up! 😊

---

*Built with ❤️ for smarter, safer investing.*
