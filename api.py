from fastapi import FastAPI
from scraper import get_latest_articles, fetch_and_store
import sqlite3
from datetime import datetime

app = FastAPI(title="Independent News API")

@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/news/latest")
def get_news(limit: int = 10, sentiment: str = None):
    """Get latest news articles
    
    Parameters:
    - limit: number of articles (default 10)
    - sentiment: filter by 'positive', 'negative', 'neutral' (optional)
    """
    articles = get_latest_articles(limit=limit, sentiment_filter=sentiment)
    
    formatted = []
    for title, summary, url, source, published, score, label in articles:
        formatted.append({
            'title': title,
            'summary': summary,
            'url': url,
            'source': source,
            'published': published,
            'sentiment_score': score,
            'sentiment_label': label
        })
    
    return {
        'count': len(formatted),
        'timestamp': datetime.now().isoformat(),
        'filter': sentiment if sentiment else 'all',
        'articles': formatted
    }

@app.get("/news/search")
def search_news(query: str, limit: int = 10):
    """Search news by keyword"""
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    
    search_term = f"%{query}%"
    c.execute('''SELECT title, summary, url, source, published, sentiment_score, sentiment_label 
                 FROM articles 
                 WHERE title LIKE ? OR summary LIKE ? 
                 ORDER BY fetched_at DESC LIMIT ?''', 
              (search_term, search_term, limit))
    
    articles = c.fetchall()
    conn.close()
    
    formatted = []
    for title, summary, url, source, published, score, label in articles:
        formatted.append({
            'title': title,
            'summary': summary,
            'url': url,
            'source': source,
            'published': published,
            'sentiment_score': score,
            'sentiment_label': label
        })
    
    return {
        'query': query,
        'count': len(formatted),
        'articles': formatted
    }

@app.get("/news/sentiment")
def get_by_sentiment(sentiment: str):
    """Get all articles by sentiment
    
    Parameters:
    - sentiment: 'positive', 'negative', or 'neutral'
    """
    if sentiment not in ['positive', 'negative', 'neutral']:
        return {'error': 'Invalid sentiment. Use: positive, negative, neutral'}
    
    articles = get_latest_articles(limit=100, sentiment_filter=sentiment)
    
    formatted = []
    for title, summary, url, source, published, score, label in articles:
        formatted.append({
            'title': title,
            'sentiment_score': score,
            'source': source,
            'url': url
        })
    
    return {
        'sentiment': sentiment,
        'count': len(formatted),
        'articles': formatted
    }

@app.post("/scrape/now")
def trigger_scrape():
    """Manually trigger a scrape run"""
    count = fetch_and_store()
    return {
        'status': 'completed',
        'new_articles': count,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
