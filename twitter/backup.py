import time
import logging
import re
import requests
from playwright.sync_api import sync_playwright, TimeoutError

# --- CONFIGURATION ---
TWITTER_USERNAME = "WatcherGuru"
CHECK_INTERVAL = 15  # seconds
X_URL = f"https://x.com/{TWITTER_USERNAME}"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1360728896428970185/jlqflxvCpNkzMMC-_lpBKnBuoKqb8hGupNGEKfRN6qAGxzutIGKh2XWYj-9J8xn45Lu-"  # your webhook

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

last_sent_tweet_id = None

# --- SEND TO DISCORD ---
def send_to_discord(tweet_text, tweet_url):
    payload = {"content": f"{tweet_text}\n\n{tweet_url}"}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Tweet sent to Discord")
        else:
            logging.warning(f"⚠️ Failed to send tweet (status: {response.status_code})")
    except Exception as e:
        logging.error(f"❌ Discord error: {e}")

# --- SCRAPER ---
def get_latest_tweet(username):
    global last_sent_tweet_id

    url = f"https://x.com/{username}"
    logging.info(f"🌐 Fetching from: {url}")

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])
            context = browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            try:
                # Wait for tweet containers to appear
                page.wait_for_selector('article', timeout=20000)
            except TimeoutError:
                page.screenshot(path="debug.png", full_page=True)
                logging.error("❌ Tweets did not load in time")
                browser.close()
                return

            # Get the first non-pinned tweet
            tweets = page.query_selector_all('article')
            if not tweets:
                logging.warning("⚠️ No tweets found on the page")
                browser.close()
                return
            
            tweet = None
            for t in tweets:
                if "Pinned" not in t.inner_text():
                    tweet = t
                    break

            if not tweet:
                logging.warning("⚠️ Only pinned tweet found, skipping...")
                browser.close()
                return

            # Extract tweet body only
            content_element = tweet.query_selector('div[data-testid="tweetText"]')
            if not content_element:
                logging.warning("⚠️ Tweet content not found")
                browser.close()
                return

            tweet_text = content_element.inner_text().strip()

            # Extract tweet URL
            tweet_url = None
            links = tweet.query_selector_all("a")
            for link in links:
                href = link.get_attribute("href")
                if href and f"/{username}/status/" in href:
                    tweet_url = f"https://x.com{href}"
                    break

            if not tweet_url:
                logging.warning("⚠️ Tweet link not found")
                browser.close()
                return

            match = re.search(r"status/(\d+)", tweet_url)
            if not match:
                logging.warning("⚠️ Could not extract Tweet ID")
                browser.close()
                return

            tweet_id = match.group(1)
            if tweet_id == last_sent_tweet_id:
                logging.info("⏩ Tweet already sent")
                browser.close()
                return

            logging.info(f"📝 New Tweet: {tweet_text}")
            logging.info(f"🔗 URL: {tweet_url}")
            send_to_discord(tweet_text, tweet_url)
            last_sent_tweet_id = tweet_id

            browser.close()

    except Exception as e:
        logging.error(f"❌ Error retrieving tweet: {e}")

# --- MAIN LOOP ---
def run_automated_check(username, interval=15):
    try:
        while True:
            logging.info("🔍 Checking for latest tweet...")
            get_latest_tweet(username)
            logging.info(f"⏳ Waiting {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("🛑 Stopping script...")

if __name__ == "__main__":
    run_automated_check(TWITTER_USERNAME, CHECK_INTERVAL)
