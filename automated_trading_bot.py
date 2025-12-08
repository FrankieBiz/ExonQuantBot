import os
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from ib_insync import *


# ============================================
# CONFIGURATION
# ============================================
class Config:
    # API Keys (USE ENVIRONMENT VARIABLES IN PRODUCTION!)
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '8d26285826f94d0e91fa073178e10600')

    # Trading Parameters
    SYMBOL = 'XOM'
    EXCHANGE = 'SMART'
    CURRENCY = 'USD'

    # Risk Management
    MAX_POSITION_SIZE = 100          # Maximum shares to hold
    POSITION_SIZE_PER_SIGNAL = 10    # Shares per trade
    MAX_DAILY_TRADES = 10
    STOP_LOSS_PCT = 0.02             # 2% stop loss
    TAKE_PROFIT_PCT = 0.03           # 3% take profit

    # Sentiment Thresholds
    STRONG_BUY_THRESHOLD = 0.3
    BUY_THRESHOLD = 0.1
    SELL_THRESHOLD = -0.1
    STRONG_SELL_THRESHOLD = -0.3

    # Timing
    NEWS_CHECK_INTERVAL = 300        # Check news every 5 minutes
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 30
    MARKET_CLOSE_HOUR = 16
    MARKET_CLOSE_MINUTE = 0

    # IB Connection
    IB_HOST = '127.0.0.1'
    IB_PORT = 7497                   # 7497 for TWS paper, 4002 for IB Gateway paper
    IB_CLIENT_ID = 1

    # Logging
    LOG_FILE = 'trading_bot.log'
    LOG_LEVEL = logging.INFO


# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QuantBot')


# ============================================
# NEWS FETCHER (uses /news/latest)
# ============================================
class NewsFetcher:
    def __init__(self, api_base_url="http://127.0.0.1:8001"):
        # Your FastAPI base URL
        self.api_base_url = api_base_url

    def fetch_latest_news(self, query, lookback_minutes=60):
        """
        Fetch latest news from your independent API.
        Ignores 'query' for now and just pulls the newest N articles.
        """
        try:
            params = {
                "limit": 20
                # you could add: "sentiment": "positive"
            }
            resp = requests.get(f"{self.api_base_url}/news/latest", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Error calling news API: {e}")
            return []

        api_articles = []
        for a in data.get("articles", []):
            api_articles.append({
                "title": a.get("title", ""),
                "description": a.get("summary", ""),
                "url": a.get("url", ""),
                "publishedAt": a.get("published", ""),
                "source": {"name": a.get("source", "")},
                "sentiment_score": a.get("sentiment_score"),
                "sentiment_label": a.get("sentiment_label"),
            })

        logger.info(f"Fetched {len(api_articles)} articles from local news API")
        return api_articles


# ============================================
# SENTIMENT ANALYZER
# ============================================
class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.important_keywords = [
            'earnings', 'profit', 'revenue', 'loss', 'lawsuit', 'merger',
            'acquisition', 'ceo', 'investigation', 'regulation', 'dividend',
            'upgrade', 'downgrade', 'analyst', 'breakthrough', 'crisis',
            'scandal', 'partnership', 'contract', 'bankruptcy', 'fraud'
        ]

    def analyze(self, text):
        """Analyze sentiment and importance of text"""
        sentiment = self.vader.polarity_scores(text)
        importance = self._calculate_importance(text)

        return {
            'compound': sentiment['compound'],
            'positive': sentiment['pos'],
            'negative': sentiment['neg'],
            'neutral': sentiment['neu'],
            'importance': importance,
            'weighted_score': sentiment['compound'] * importance
        }

    def _calculate_importance(self, text):
        """Calculate article importance based on keywords and length"""
        text_lower = text.lower()

        # Base score
        score = 1.0

        # Keyword matching
        keyword_matches = sum(1 for keyword in self.important_keywords if keyword in text_lower)
        score += keyword_matches * 0.5

        # Length bonus
        if len(text) > 100:
            score += 0.3
        if len(text) > 200:
            score += 0.3

        return min(score, 3.0)  # Cap at 3.0

    def aggregate_sentiment(self, articles, time_decay_hours=24):
        """Aggregate sentiment from multiple articles with time decay"""
        if not articles:
            return 0.0

        total_weighted_score = 0.0
        total_weight = 0.0
        now = datetime.now()

        for article in articles:
            analysis = self.analyze(article.get('title', '') + ' ' + article.get('description', ''))

            # Calculate time decay
            try:
                pub_time = datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00'))
                hours_old = (now - pub_time.replace(tzinfo=None)).total_seconds() / 3600
                decay_factor = max(0.1, 1 - (hours_old / time_decay_hours))
            except Exception:
                decay_factor = 0.5

            weight = analysis['importance'] * decay_factor
            total_weighted_score += analysis['compound'] * weight
            total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0


# ============================================
# TRADING STRATEGY
# ============================================
class TradingStrategy:
    def __init__(self, config):
        self.config = config
        self.daily_trades = 0
        self.last_trade_date = None
        self.position = 0
        self.entry_price = 0.0
        self.trades_history = []

    def reset_daily_counter(self):
        """Reset daily trade counter"""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_trades = 0
            self.last_trade_date = today

    def generate_signal(self, sentiment_score, current_price):
        """Generate trading signal based on sentiment"""
        self.reset_daily_counter()

        # Check if we've hit daily trade limit
        if self.daily_trades >= self.config.MAX_DAILY_TRADES:
            logger.info("Daily trade limit reached")
            return None, 0

        # Check risk management rules
        if self.position != 0:
            pnl_pct = (current_price - self.entry_price) / self.entry_price

            # Stop loss
            if pnl_pct <= -self.config.STOP_LOSS_PCT:
                logger.warning(f"Stop loss triggered! PnL: {pnl_pct:.2%}")
                return 'CLOSE', abs(self.position)

            # Take profit
            if pnl_pct >= self.config.TAKE_PROFIT_PCT:
                logger.info(f"Take profit triggered! PnL: {pnl_pct:.2%}")
                return 'CLOSE', abs(self.position)

        # Generate signal based on sentiment
        signal = None
        quantity = 0

        if sentiment_score >= self.config.STRONG_BUY_THRESHOLD:
            if self.position < self.config.MAX_POSITION_SIZE:
                signal = 'BUY'
                quantity = min(
                    self.config.POSITION_SIZE_PER_SIGNAL * 2,
                    self.config.MAX_POSITION_SIZE - self.position
                )

        elif sentiment_score >= self.config.BUY_THRESHOLD:
            if self.position < self.config.MAX_POSITION_SIZE:
                signal = 'BUY'
                quantity = min(
                    self.config.POSITION_SIZE_PER_SIGNAL,
                    self.config.MAX_POSITION_SIZE - self.position
                )

        elif sentiment_score <= self.config.STRONG_SELL_THRESHOLD:
            if self.position > 0:
                signal = 'SELL'
                quantity = min(
                    self.config.POSITION_SIZE_PER_SIGNAL * 2,
                    self.position
                )

        elif sentiment_score <= self.config.SELL_THRESHOLD:
            if self.position > 0:
                signal = 'SELL'
                quantity = min(self.config.POSITION_SIZE_PER_SIGNAL, self.position)

        return signal, quantity

    def record_trade(self, signal, quantity, price):
        """Record trade execution"""
        self.daily_trades += 1

        if signal == 'BUY':
            self.position += quantity
            self.entry_price = price
        elif signal in ('SELL', 'CLOSE'):
            self.position -= quantity
            if self.position == 0:
                self.entry_price = 0.0

        self.trades_history.append({
            'timestamp': datetime.now(),
            'signal': signal,
            'quantity': quantity,
            'price': price,
            'position': self.position
        })

        logger.info(f"Trade executed: {signal} {quantity} @ ${price:.2f} | Position: {self.position}")


# ============================================
# INTERACTIVE BROKERS TRADER
# ============================================
class IBTrader:
    def __init__(self, config):
        self.config = config
        self.ib = IB()
        self.connected = False
        self.contract = Stock(config.SYMBOL, config.EXCHANGE, config.CURRENCY)

    def connect(self):
        """Connect to Interactive Brokers"""
        try:
            self.ib.connect(self.config.IB_HOST, self.config.IB_PORT, self.config.IB_CLIENT_ID)
            self.connected = True
            logger.info("Connected to Interactive Brokers")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IB: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from Interactive Brokers")

    def get_current_price(self):
        """Get current market price"""
        try:
            ticker = self.ib.reqMktData(self.contract)
            self.ib.sleep(1)  # Wait for data
            price = ticker.marketPrice()
            if price > 0:
                return price
            else:
                # Fallback to last price
                return ticker.last if ticker.last > 0 else None
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None

    def place_order(self, action, quantity):
        """Place market order"""
        try:
            order = MarketOrder(action, quantity)
            trade = self.ib.placeOrder(self.contract, order)

            # Wait for fill
            timeout = 30
            start_time = time.time()
            while not trade.isDone() and (time.time() - start_time) < timeout:
                self.ib.sleep(0.5)

            if trade.isDone():
                logger.info(f"Order filled: {action} {quantity} {self.config.SYMBOL}")
                return True
            else:
                logger.warning(f"Order timeout: {action} {quantity} {self.config.SYMBOL}")
                return False

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return False

    def get_position(self):
        """Get current position"""
        try:
            positions = self.ib.positions()
            for pos in positions:
                if pos.contract.symbol == self.config.SYMBOL:
                    return int(pos.position)
            return 0
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return 0


# ============================================
# MAIN TRADING BOT
# ============================================
class QuantTradingBot:
    def __init__(self):
        self.config = Config()
        self.news_fetcher = NewsFetcher()  # uses http://127.0.0.1:8001 by default
        self.sentiment_analyzer = SentimentAnalyzer()
        self.strategy = TradingStrategy(self.config)
        self.trader = IBTrader(self.config)
        self.running = False

    def is_market_open(self):
        """TEMP: Always treat market as open for testing."""
        return True

    def run_trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # 1. Fetch latest news
            logger.info("Fetching latest news...")
            articles = self.news_fetcher.fetch_latest_news(
                f"{self.config.SYMBOL} Exxon Mobil",
                lookback_minutes=self.config.NEWS_CHECK_INTERVAL // 60
            )

            if not articles:
                logger.info("No new articles found")
                return

            # 2. Analyze sentiment
            logger.info(f"Analyzing sentiment for {len(articles)} articles...")
            scores = [a.get("sentiment_score") for a in articles if a.get("sentiment_score") is not None]
            if scores:
                sentiment_score = sum(scores) / len(scores)
                logger.info(f"Aggregate sentiment score (from API): {sentiment_score:.3f}")
            else:
                sentiment_score = self.sentiment_analyzer.aggregate_sentiment(articles)
                logger.info(f"Aggregate sentiment score (local VADER): {sentiment_score:.3f}")

            # 3. Get current price
            current_price = self.trader.get_current_price()
            if current_price is None:
                logger.error("Could not get current price")
                return

            logger.info(f"Current price: ${current_price:.2f}")

            # 4. Generate trading signal
            signal, quantity = self.strategy.generate_signal(sentiment_score, current_price)

            if signal and quantity > 0:
                logger.info(f"Signal generated: {signal} {quantity} shares")

                # 5. Execute trade
                action = 'BUY' if signal == 'BUY' else 'SELL'
                success = self.trader.place_order(action, quantity)

                if success:
                    self.strategy.record_trade(signal, quantity, current_price)
                    logger.info(f"Trade successful! Position: {self.strategy.position}")
                else:
                    logger.error("Trade execution failed")
            else:
                logger.info("No signal generated or invalid quantity")

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)

    def start(self):
        """Start the trading bot"""
        logger.info("=" * 50)
        logger.info("QUANTITATIVE TRADING BOT STARTING")
        logger.info("=" * 50)
        logger.info(f"Symbol: {self.config.SYMBOL}")
        logger.info(f"News check interval: {self.config.NEWS_CHECK_INTERVAL}s")
        logger.info(f"Max position size: {self.config.MAX_POSITION_SIZE}")
        logger.info("=" * 50)

        # Connect to IB
        if not self.trader.connect():
            logger.error("Failed to connect to Interactive Brokers. Exiting.")
            return

        self.running = True

        try:
            while self.running:
                if self.is_market_open():
                    logger.info("Market is OPEN - Running trading cycle")
                    self.run_trading_cycle()
                else:
                    logger.info("Market is CLOSED - Waiting...")

                logger.info(f"Sleeping for {self.config.NEWS_CHECK_INTERVAL}s...")
                time.sleep(self.config.NEWS_CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.running = False

        # Save trade history
        if self.strategy.trades_history:
            df = pd.DataFrame(self.strategy.trades_history)
            df.to_csv('trade_history.csv', index=False)
            logger.info(f"Saved {len(self.strategy.trades_history)} trades to trade_history.csv")

        # Disconnect from IB
        self.trader.disconnect()
        logger.info("Trading bot stopped")


# ============================================
# ENTRY POINT
# ============================================
if __name__ == "__main__":
    bot = QuantTradingBot()
    bot.start()
