from langdetect import detect
from textblob import TextBlob

# Load your headlines from the file
with open("exxon_news.txt", "r", encoding="utf-8") as f:
    headlines = f.readlines()

# Processing
results = []
for line in headlines:
    text = line.strip()
    try:
        lang = detect(text)
        if lang == "en":
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            # Assign label based on polarity
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            results.append((text, sentiment))
    except Exception as e:
        pass  # skip lines that can't be detected

# Save results to a new file
with open("exxon_news_labeled.txt", "w", encoding="utf-8") as f:
    for headline, sentiment in results:
        f.write(f"{sentiment}\t{headline}\n")

print(f"Done! {len(results)} headlines labeled and saved to exxon_news_labeled.txt.")
