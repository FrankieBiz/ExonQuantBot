import pandas as pd
import yfinance as yf
from collections import defaultdict
from datetime import datetime

# === 1. COLLECT DAILY SENTIMENT === #
daily = defaultdict(lambda: {'positive':0, 'negative':0, 'neutral':0})
with open('exxon_news_labeled.txt', 'r', encoding='utf-8') as f:
    for line in f:
        # Expects lines like: sentiment\tYYYY-MM-DDTHH:MM...\theadline
        parts = line.strip().split('\t')
        if len(parts) >= 3:
            sentiment, published, headline = parts[0], parts[1], parts[2]
            # Get YYYY-MM-DD from published
            try:
                day = published[:10]
            except:
                continue
            daily[day][sentiment] += 1

# Make into DataFrame
sentiment_df = pd.DataFrame([
    {'date': day, 
     'pos': vals['positive'],
     'neg': vals['negative'],
     'neu': vals['neutral'],
     'sentiment_score': vals['positive'] - vals['negative']}
    for day, vals in daily.items()
])
sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])

# === 2. GET HISTORICAL PRICE DATA === #
start = sentiment_df['date'].min().strftime('%Y-%m-%d')
end = sentiment_df['date'].max().strftime('%Y-%m-%d')
prices = yf.download('XOM', start=start, end=end)
prices = pd.DataFrame(prices).copy()
prices.reset_index(inplace=True)         # GUARANTEED to flatten index
if 'Date' in prices.columns:
    prices_use = prices[['Date', 'Close']].copy()
    prices_use.columns = ['date', 'close']
else:
    # fallback for alternate yfinance output
    prices_use = prices[['index', 'Close']].copy()
    prices_use.columns = ['date', 'close']
prices_use['date'] = pd.to_datetime(prices_use['date'])


# === 3. ALIGN AND BACKTEST === #
combined = pd.merge(prices_use, sentiment_df, on='date', how='left').fillna(0)

# Simple trading logic: signal = 1 if sentiment > 0, -1 if < 0, 0 if neutral
def get_signal(row):
    if row['sentiment_score'] > 0:
        return 1 # BUY
    elif row['sentiment_score'] < 0:
        return -1 # SELL
    else:
        return 0 # HOLD
combined['signal'] = combined.apply(get_signal, axis=1)

# Simulated returns: change only when signal changes
combined['daily_return'] = combined['close'].pct_change()
combined['strategy_return'] = combined['signal'].shift(1) * combined['daily_return']
combined['cum_strategy'] = (1 + combined['strategy_return'].fillna(0)).cumprod()
combined['cum_buyhold'] = (1 + combined['daily_return'].fillna(0)).cumprod()

print(combined[['date','close','sentiment_score','signal','cum_strategy','cum_buyhold']].tail(10))

# Save to CSV for further analysis or plotting
combined.to_csv('sentiment_backtest_results.csv', index=False)
print('Backtest complete. Results saved in sentiment_backtest_results.csv')
