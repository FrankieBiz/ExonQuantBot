from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def get_sentiment_score(headline):
    return analyzer.polarity_scores(headline)['compound']

def rank_importance(headline):
    keywords = ['earnings', 'lawsuit', 'merger', 'acquisition', 'ceo', 'investigation', 'profit', 'regulation']
    score = 1 if len(headline) > 40 else 0
    score += sum(1 for word in keywords if word in headline.lower())
    return score

# Example headlines
headlines = [
    "Exxon CEO faces lawsuit over merger decision",
    "Exxon Mobil profits surge on strong earnings report",
    "Exxon accused of pollution violation by EPA"
]

for headline in headlines:
    sent_score = get_sentiment_score(headline)
    importance = rank_importance(headline)
    print(f"Headline: {headline}")
    print(f"  Sentiment: {sent_score:.2f}, Importance: {importance}")
