import schedule
import time
from scraper import fetch_and_store
from datetime import datetime

def job():
    """Run the scraper"""
    print(f"\n{'='*60}")
    print(f"📰 SCRAPER RUN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    fetch_and_store()

# Schedule every 5 minutes
schedule.every(5).minutes.do(job)

print("🚀 Scheduler started. Scraping every 5 minutes...")
print("Press Ctrl+C to stop.\n")

# Run initial job
job()

# Keep running
try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
except KeyboardInterrupt:
    print("\n⏹ Scheduler stopped.")
