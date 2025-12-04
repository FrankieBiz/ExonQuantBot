import feedparser
import sqlite3
import hashlib
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# RSS feeds for finance news
FEEDS = {
    'bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
    'reuters': 'https://feeds.reuters.com/reuters/businessNews',
    'cnbc': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114'
}

def init_db():
    """Create SQLite database for storing articles"""
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY, 
                  url_hash TEXT UNIQUE, 
                  title TEXT, 
                  summary TEXT, 
                  url TEXT,
                  source TEXT, 
                  published TEXT,
                  sentiment_score REAL,
                  sentiment_label TEXT,
                  fetched_at TEXT)''')
    conn.commit()
    conn.close()

def analyze_sentiment(text):
    """Analyze sentiment and return score + label"""
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # Label: positive, neutral, negative
    if compound >= 0.05:
        label = 'positive'
    elif compound <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'
    
    return compound, label

def fetch_and_store(max_articles=50):
    """Fetch all RSS feeds, analyze sentiment, and store new articles"""
    init_db()
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    new_count = 0
    
    for source_name, feed_url in FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            print(f"✓ {source_name}: {len(feed.entries)} articles found")
            
            for entry in feed.entries[:20]:  # Top 20 per feed
                url_hash = hashlib.md5(entry.get('link', '').encode()).hexdigest()
                
                # Combine title + summary for sentiment analysis
                text_to_analyze = entry.get('title', '') + ' ' + entry.get('summary', '')
                sentiment_score, sentiment_label = analyze_sentiment(text_to_analyze)
                
                try:
                    c.execute('''INSERT INTO articles 
                                (url_hash, title, summary, url, source, published, 
                                 sentiment_score, sentiment_label, fetched_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (url_hash,
                              entry.get('title', ''),
                              entry.get('summary', '')[:500],
                              entry.get('link', ''),
                              source_name,
                              entry.get('published', ''),
                              sentiment_score,
                              sentiment_label,
                              datetime.now().isoformat()))
                    new_count += 1
                    print(f"  → {sentiment_label.upper()} ({sentiment_score:.2f}): {entry.get('title', '')[:60]}...")
                except sqlite3.IntegrityError:
                    pass  # Duplicate, skip
        except Exception as e:
            print(f"✗ {source_name} failed: {e}")
    
    conn.commit()
    conn.close()
    print(f"\n→ Stored {new_count} new articles\n")
    return new_count

def get_latest_articles(limit=10, sentiment_filter=None):
    """Retrieve latest articles from database
    sentiment_filter: 'positive', 'negative', 'neutral', or None for all
    """
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    if sentiment_filter:
        c.execute('''SELECT title, summary, url, source, published, sentiment_score, sentiment_label 
                     FROM articles 
                     WHERE sentiment_label = ? 
                     ORDER BY fetched_at DESC LIMIT ?''', 
                  (sentiment_filter, limit))
    else:
        c.execute('''SELECT title, summary, url, source, published, sentiment_score, sentiment_label 
                     FROM articles 
                     ORDER BY fetched_at DESC LIMIT ?''', (limit,))
    
    articles = c.fetchall()
    conn.close()
    return articles

if __name__ == "__main__":
    fetch_and_store()
    print("Latest 5 articles (all):")
    for title, summary, url, source, published, score, label in get_latest_articles(5):
        print(f"\n[{label.upper()} {score:.2f}] {source.upper()}: {title}")
        print(f"  {url}")
