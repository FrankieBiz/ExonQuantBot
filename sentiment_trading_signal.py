from collections import defaultdict
from datetime import datetime

sentiment_file = "exxon_news_labeled.txt"
daily = defaultdict(lambda: {'positive':0, 'negative':0, 'neutral':0})

with open(sentiment_file, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split('\t')
        # If the date is included in the headline tab, extract it; else use today
        if len(parts) == 2:
            sentiment, headline = parts
            date_str = datetime.today().strftime('%Y-%m-%d')
        elif len(parts) == 3:
            sentiment, date_str, headline = parts
        else:
            continue
        # You may need to refine this based on your actual file format
        daily[date_str][sentiment] += 1

for date, counts in sorted(daily.items()):
    if counts['positive'] > counts['negative']:
        signal = 'BUY'
    elif counts['negative'] > counts['positive']:
        signal = 'SELL'
    else:
        signal = 'HOLD'
    print(f"{date}\tPos:{counts['positive']}\tNeg:{counts['negative']}\tSignal:{signal}")
