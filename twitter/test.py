import time
import logging
import re
import requests
from playwright.sync_api import sync_playwright, TimeoutError

# --- CONFIGURATION ---
TWITTER_USERNAME = "WatcherGuru"
CHECK_INTERVAL = 15  # seconds
X_URL = f"https://x.com/{TWITTER_USERNAME}"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1360728896428970185/jlqflxvCpNkzMMC-_lpBKnBuoKqb8hGupNGEKfRN6qAGxzutIGKh2XWYj-9J8xn45Lu-"
#DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1360652670037131295/6KxXXaiwEzn__1Wub25k2mn8AWWKsiVU2Vk7h2nfGtmR79oT4BuI2zRk3bOmIB861KVl"
# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

last_sent_tweet_id = None

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

def capture_screenshot(page, tweet_index):
    screenshot_path = f"screenshot_{tweet_index}.png"
    page.screenshot(path=screenshot_path)
    logging.info(f"📸 Screenshot taken and saved as {screenshot_path}")

def extract_latest_tweet(page, username):
    global last_sent_tweet_id

    try:
        page.reload(wait_until="domcontentloaded", timeout=15000)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)
        page.wait_for_selector("article", timeout=15000)
        tweet_articles = page.query_selector_all("article")

        # Scroll until we have at least 5 tweet articles
        max_scrolls = 5
        for _ in range(max_scrolls):
            page.mouse.wheel(0, 600)  # Scroll down
            time.sleep(1.5)  # Wait for tweets to load
            tweet_articles = page.query_selector_all("article")
            if len(tweet_articles) > 4:  # Ensure we have more than 4 tweets
                break

        # Loop through the articles and find the latest non-pinned tweet
        for i, article in enumerate(tweet_articles):
            print(f"\n--- Article {i} ---\n{article.inner_text()}\n")
            try:
                inner = article.inner_text()

                # Skip if pinned or contains no real tweet text
                if "Pinned Tweet" in inner or "Pinned" in inner:
                    logging.info(f"📌 Skipping pinned tweet at index {i}")
                    continue

                tweet_text_element = article.query_selector('div[lang]')
                if not tweet_text_element:
                    logging.info(f"⚠️ Skipping non-tweet at index {i} (no text)")
                    continue

                tweet_text = tweet_text_element.inner_text().strip()

                # Extract tweet URL
                tweet_url = None
                links = article.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and f"/{username}/status/" in href:
                        tweet_url = f"https://x.com{href}"
                        break

                if not tweet_url:
                    logging.info(f"⚠️ Skipping tweet at index {i} (no URL)")
                    continue

                tweet_id_match = re.search(r"status/(\d+)", tweet_url)
                if not tweet_id_match:
                    logging.info(f"⚠️ Skipping tweet at index {i} (no ID)")
                    continue

                tweet_id = tweet_id_match.group(1)

                if tweet_id == last_sent_tweet_id:
                    logging.info(f"⏩ Tweet already sent (ID: {tweet_id})")
                    return

                # ✅ FIRST valid non-pinned tweet found!
                logging.info(f"📝 New Tweet Found at index {i}: {tweet_text}")
                logging.info(f"🔗 URL: {tweet_url}")
                send_to_discord(tweet_text, tweet_url)
                last_sent_tweet_id = tweet_id

                # Capture a screenshot of the page
                capture_screenshot(page, i)

                return

            except Exception as inner_e:
                logging.warning(f"⚠️ Skipping article at index {i} due to error: {inner_e}")
                continue

        logging.info("🔍 No new unpinned tweet found.")

    except TimeoutError:
        logging.error("❌ Timeout while loading tweets")
    except Exception as e:
        logging.error(f"❌ Error during tweet check: {e}")

def run_monitor_loop():
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115 Safari/537.36"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-gpu", "--no-sandbox"])
        context = browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 800})
        page = context.new_page()
        

        try:
            while True:
                logging.info("🔍 Checking for latest tweet...")
                page.goto(X_URL, wait_until="domcontentloaded", timeout=30000)

            # Optional: Trigger lazy load
                page.mouse.wheel(0, 2000)
                time.sleep(2)

                extract_latest_tweet(page, TWITTER_USERNAME)
                logging.info(f"⏳ Waiting {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logging.info("🛑 Stopping...")
        finally:
            browser.close()

if __name__ == "__main__":
    run_monitor_loop()
