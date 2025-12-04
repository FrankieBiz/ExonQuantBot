***

# ExonQuantBot

An automated, news‑driven quant trading bot for **XOM (Exxon Mobil)** that:

- Scrapes finance news from multiple RSS feeds (Bloomberg, CNBC, etc.)
- Analyzes sentiment with **VADER**
- Stores articles + sentiment in **SQLite**
- Exposes the data via a local **FastAPI** server
- Uses that sentiment to generate buy/sell signals
- Sends trades to **Interactive Brokers** via `ib_insync`

This guide is for **Windows users** and assumes **no prior experience**.

***

## Table of Contents

- [0. Requirements](#0-requirements)
- [1. Download the Project](#1-download-the-project)
- [2. Folder Overview](#2-folder-overview)
- [Part A – News Scraper + API Only](#part-a--news-scraper--api-only)
  - [3. Create Scraper Environment](#3-create-scraper-environment)
  - [4. Install Scraper Dependencies](#4-install-scraper-dependencies)
  - [5. Run Scraper Once](#5-run-scraper-once)
  - [6. Run Scheduler (Every 5 Minutes)](#6-run-scheduler-every-5-minutes)
  - [7. Run FastAPI Server](#7-run-fastapi-server)
  - [8. Test the API](#8-test-the-api)
- [Part B – Full Trading Bot with Interactive Brokers](#part-b--full-trading-bot-with-interactive-brokers)
  - [9. Create Trading Environment](#9-create-trading-environment)
  - [10. Install TWS and Enable API](#10-install-tws-and-enable-api)
  - [11. Run the Trading Bot](#11-run-the-trading-bot)
- [12. Stopping Everything](#12-stopping-everything)
- [13. Common Problems & Fixes](#13-common-problems--fixes)

***

## 0. Requirements

### 0.1. Operating System

- Windows 10 or 11

### 0.2. Python (Anaconda recommended)

1. Download **Anaconda Individual Edition** for Windows.
2. Run the installer:
   - Choose “Just Me”
   - Use default install location
3. After installation:
   - Press Windows key
   - Search for **“Anaconda Prompt”**
   - Open it

You will use **Anaconda Prompt** for most commands.

***

## 1. Download the Project

1. In your browser, go to:  
   `https://github.com/FrankieBiz/ExonQuantBot`
2. Click the green **“Code”** button.
3. Click **“Download ZIP”**.
4. When the download finishes:
   - Right‑click the ZIP file
   - Choose **“Extract All…”**
   - Extract to a simple path, for example:  
     `C:\Users\YOURNAME\Desktop\ExonQuantBot`

Replace `YOURNAME` with your Windows username.

From now on, we’ll assume the project is at:

```text
C:\Users\YOURNAME\Desktop\ExonQuantBot
```

***

## 2. Folder Overview

Inside `ExonQuantBot`, you should see (among others):

- `NewScraper/`
  - `scraper.py` – fetches news + sentiment, stores in `news.db`
  - `scheduler.py` – runs scraper every 5 minutes
  - `api.py` – FastAPI server to query the news and sentiment
- `automated_trading_bot.py` – main trading bot using Interactive Brokers and your API
- `trading_bot.log` – log file for bot runs (created after running)
- `trade_history.csv` – saved trades (created after trades occur)

***

# Part A – News Scraper + API Only

Goal: run just the **news system** so you can scrape, store, and query sentiment‑tagged news, without any trading.

***

## 3. Create Scraper Environment

1. Open **Anaconda Prompt**.
2. Go to the `NewScraper` folder:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot\NewScraper
```

3. Create a virtual environment named `venv`:

```bat
python -m venv venv
```

4. Activate it:

```bat
venv\Scripts\activate
```

You should now see `(venv)` at the start of the line in the prompt.

5. Upgrade `pip`:

```bat
python -m pip install --upgrade pip
```

***

## 4. Install Scraper Dependencies

With `(venv)` active and still in `NewScraper`, run:

```bat
pip install feedparser vaderSentiment fastapi "uvicorn[standard]" schedule
```

What each package is for:

- `feedparser` – read RSS feeds
- `vaderSentiment` – sentiment analysis
- `fastapi` – build the API
- `uvicorn[standard]` – web server for FastAPI
- `schedule` – schedule scraper runs every X minutes

***

## 5. Run Scraper Once

This will fetch news, analyze sentiment, and create the database.

In the same `(venv)`:

```bat
python scraper.py
```

You should see output similar to:

```text
✓ bloomberg: 30 articles found
✓ cnbc: 39 articles found

→ Stored 40 new articles

Latest 5 articles (all):

[POSITIVE 0.69] ...
[NEGATIVE -0.10] ...
...
```

You should now have a `news.db` file in `NewScraper` – this is your SQLite database.

***

## 6. Run Scheduler (Every 5 Minutes)

Now we’ll set up continuous scraping.

Still in `NewScraper` with `(venv)`:

```bat
python scheduler.py
```

You should see:

```text
🚀 Scheduler started. Scraping every 5 minutes...
Press Ctrl+C to stop.

============================================================
📰 SCRAPER RUN: 2025-12-02 19:16:25
============================================================
✓ bloomberg: 30 articles found
✓ cnbc: 30 articles found
→ Stored 0 new articles
```

Leave this window **open** while you want news to keep updating.

To stop the scheduler: press `Ctrl + C`.

***

## 7. Run FastAPI Server

Open a **second** Anaconda Prompt window.

1. Go to `NewScraper`:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot\NewScraper
```

2. Activate the same `venv`:

```bat
venv\Scripts\activate
```

3. Start the FastAPI server:

```bat
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

You want to see:

```text
Uvicorn running on http://0.0.0.0:8001
Application startup complete.
```

Keep this window **open**. This is your news API.

***

## 8. Test the API

On the same PC, open a web browser and go to:

```text
http://localhost:8001/docs
```

You should see the interactive API docs.

Try these:

1. **GET /health**
   - Click it
   - Click **“Try it out”**
   - Click **“Execute”**
   - You should see `{"status": "ok", ...}`

2. **GET /news/latest**
   - Click it
   - “Try it out”
   - Set `limit` to `5`
   - Execute
   - You should get 5 recent articles with titles, summaries, URLs, sentiment.

3. **GET /news/latest?sentiment=positive**
   - Set `sentiment` to `positive`
   - Execute
   - You get only positive‑sentiment articles.

4. **GET /news/search**
   - Set `query` to `AI` or `oil` or `Exxon`
   - Execute
   - You get only articles matching that keyword.

At this point, **Part A (news scraper + API)** is fully working.

You can stop here if you just want the news system.

***

# Part B – Full Trading Bot with Interactive Brokers

Now we’ll connect everything to a trading bot that:

- Fetches news from your FastAPI API
- Aggregates sentiment
- Gets live prices from Interactive Brokers (IBKR)
- Places trades based on the sentiment

Important: use **Paper Trading** while testing.

***

## 9. Create Trading Environment

We’ll create a separate virtual environment for the trading bot.

1. Open a **third** Anaconda Prompt.
2. Go to the project root:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot
```

3. Create a virtual environment called `trading-venv`:

```bat
python -m venv trading-venv
```

4. Activate it:

```bat
trading-venv\Scripts\activate
```

5. Install required packages:

```bat
pip install ib_insync pandas requests vaderSentiment
```

- `ib_insync` – talk to Interactive Brokers
- `pandas` – store trade history
- `requests` – call your FastAPI news API
- `vaderSentiment` – extra safety (used in the bot too)

***

## 10. Install TWS and Enable API

### 10.1. Install Trader Workstation (TWS)

1. Download **Trader Workstation (TWS)** for Windows.
2. Install it.
3. Log in with:
   - Your **Paper Trading** account (recommended for testing)

### 10.2. Enable API Access in TWS

Inside TWS:

1. Go to `File` → `Global Configuration`.
2. On the left, click `API` → `Settings`.
3. Check:
   - “Enable ActiveX and Socket Clients”
4. Set:
   - Socket port: `7497`
5. Optionally, check “Read‑Only API” while testing to prevent order placement (if you just want to see that it connects).

Make sure TWS is **running and logged in** before you start the bot.

***

## 11. Run the Trading Bot

At this point, you should have:

- Window 1: `scheduler.py` running (scraper, `(venv)` active)
- Window 2: `uvicorn api:app ...` running (FastAPI, `(venv)` active)
- TWS: open, logged in to paper account

Now in **Window 3** (trading environment):

1. Ensure you’re in the project root and `trading-venv` is active:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot
trading-venv\Scripts\activate
```

2. Run the bot:

```bat
python automated_trading_bot.py
```

Watch the output. You should see something like:

```text
==================================================
QUANTITATIVE TRADING BOT STARTING
==================================================
Symbol: XOM
News check interval: 300s
Max position size: 100
==================================================
Connected to Interactive Brokers
Market is OPEN - Running trading cycle
Fetching latest news...
Fetched 20 articles from local news API
Analyzing sentiment for 20 articles...
Aggregate sentiment score (from API): 0.123
Current price: $XX.XX
Signal generated: BUY 10 shares
Order filled: BUY 10 XOM
Trade successful! Position: 10
Sleeping for 300s...
```

If the market is closed, you’ll instead see:

```text
Market is CLOSED - Waiting...
Sleeping for 300s...
```

The bot will automatically:

- Check if market hours (9:30–16:00 ET, Mon–Fri)
- Fetch news from `http://localhost:8001`
- Compute a sentiment score
- Decide to BUY / SELL / CLOSE
- Send orders through Interactive Brokers using `ib_insync`

***

## 12. Stopping Everything

To shut down:

- **Trading bot:**  
  In Window 3 – press `Ctrl + C`.

- **API server:**  
  In Window 2 – press `Ctrl + C`.

- **Scheduler:**  
  In Window 1 – press `Ctrl + C`.

- **TWS:**  
  Close the TWS application.

After stopping:

- Check `trade_history.csv` for executed trades.
- Check `trading_bot.log` for a detailed log of the run.

***

## 13. Common Problems & Fixes

### 13.1. `'uvicorn' is not recognized as an internal or external command`

Cause: `uvicorn` not installed in the active environment, or environment not active.

Fix:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot\NewScraper
venv\Scripts\activate
pip install "uvicorn[standard]"
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

***

### 13.2. `ModuleNotFoundError: No module named 'ib_insync'`

Cause: `ib_insync` not installed in `trading-venv`.

Fix:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot
trading-venv\Scripts\activate
pip install ib_insync
```

***

### 13.3. `Error calling news API: Failed to establish a new connection`

Cause: FastAPI server is not running, or wrong port.

Fix:

- Make sure Window 2 is running:

```bat
cd C:\Users\YOURNAME\Desktop\ExonQuantBot\NewScraper
venv\Scripts\activate
python -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

***

### 13.4. Bot says “No new articles found”

Possibilities:

- Scraper/scheduler hasn’t run yet → run `python scraper.py` once, or wait for next `scheduler` run.
- `news.db` was deleted or empty → run `python scraper.py` manually first.

***
