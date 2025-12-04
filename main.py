import feedparser

# Try a different, more reliable finance RSS feed
url = "https://feeds.bloomberg.com/markets/news.rss"
feed = feedparser.parse(url)

print(f"Feed title: {feed.feed.get('title', 'No title')}")
print(f"Found {len(feed.entries)} entries\n")

if feed.entries:
    print("First entry keys:", feed.entries[0].keys())
    print("\nFirst entry content:")
    entry = feed.entries[0]
    print(f"  Title: {entry.get('title', 'N/A')}")
    print(f"  Link: {entry.get('link', 'N/A')}")
    print(f"  Published: {entry.get('published', 'N/A')}")
    print(f"  Summary: {entry.get('summary', 'N/A')[:100]}...")
else:
    print("No entries found")
