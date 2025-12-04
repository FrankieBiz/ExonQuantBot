import requests

api_key = "8d26285826f94d0e91fa073178e10600"  # <-- Your real NewsAPI key
topic = "Exxon Mobil"
page_size = 100  # Max per NewsAPI request (free tier)
max_pages = 5    # Up to 5 pages = 500 articles

all_headlines = []

for page in range(1, max_pages+1):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={topic.replace(' ', '+')}"
        f"&sortBy=publishedAt&pageSize={page_size}&page={page}&language=en&apiKey={api_key}"
    )
    response = requests.get(url)
    try:
        data = response.json()
    except Exception as e:
        print(f"Error parsing response for page {page}: {e}")
        continue
    articles = data.get("articles", [])
    if not articles:
        break  # No more articles returned
    for article in articles:
        headline = article.get("title", "")
        published = article.get("publishedAt", "")
        all_headlines.append(f"{published}\t{headline}")
    print(f"Fetched {len(articles)} articles from page {page}")

# Save all headlines to file
with open("exxon_news.txt", "w", encoding="utf-8") as f:
    for line in all_headlines:
        f.write(line + "\n")

print(f"Done! {len(all_headlines)} headlines saved to exxon_news.txt.")
