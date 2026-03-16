import requests
import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
TWITTER_USERNAME = "WatcherGuru"
CHECK_INTERVAL = 15  # seconds
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
#DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1360652670037131295/6KxXXaiwEzn__1Wub25k2mn8AWWKsiVU2Vk7h2nfGtmR79oT4BuI2zRk3bOmIB861KVl"
#saját DC: 
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1360728896428970185/jlqflxvCpNkzMMC-_lpBKnBuoKqb8hGupNGEKfRN6qAGxzutIGKh2XWYj-9J8xn45Lu-"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- GLOBALS ---
driver = None
last_sent_tweet_id = None

# --- CHROME OPTIONS ---
def get_chrome_options():
    options = Options()
    
    return options

# --- DISCORD SEND ---
def send_to_discord(tweet_text, tweet_url):
    payload = {
        "content": f"{tweet_text}\n\n{tweet_url}"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Tweet sent to Discord")
        else:
            logging.warning(f"⚠️ Failed to send tweet (status: {response.status_code})")
    except Exception as e:
        logging.error(f"❌ Discord error: {e}")

# --- DRIVER CONTROL ---
def restart_driver(retries=3, delay=5):
    global driver
    logging.info("🔄 Restarting WebDriver...")
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None

    for attempt in range(1, retries + 1):
        try:
            service = Service(CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=get_chrome_options())
            logging.info("✅ WebDriver restarted")
            return
        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {e}")
            time.sleep(delay)
    
    raise RuntimeError("❌ WebDriver could not be restarted after multiple attempts")

# --- TWEET SCRAPER ---
def get_latest_tweet(username):
    global driver, last_sent_tweet_id

    if not driver:
        restart_driver()

    try:
        driver.get(f"https://twitter.com/{username}")
        

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )

        tweet_element = None
        tweet_articles = driver.find_elements(By.CSS_SELECTOR, "article")

        for article in tweet_articles:
            try:
                if "Pinned" in article.text:
                    logging.info("📌 Skipping pinned tweet...")
                    continue

                # Try to extract tweet text safely
                tweet_text_element = WebDriverWait(article, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[lang]"))
                )
                tweet_text = tweet_text_element.text.strip()

                # Safely grab the tweet URL
                tweet_url = None
                links = article.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and f"/{username}/status/" in href:
                        tweet_url = href
                        break

                if not tweet_url:
                    logging.warning("⚠️ Tweet URL not found")
                    return

                tweet_id_match = re.search(r"status/(\d+)", tweet_url)
                if not tweet_id_match:
                    logging.warning("⚠️ Tweet ID not found")
                    return

                tweet_id = tweet_id_match.group(1)

                if tweet_id == last_sent_tweet_id:
                    logging.info("⏩ Tweet already sent")
                    return

                logging.info(f"📝 New Tweet: {tweet_text}")
                logging.info(f"🔗 URL: {tweet_url}")
                send_to_discord(tweet_text, tweet_url)
                last_sent_tweet_id = tweet_id
                return
            except Exception as inner_e:
                logging.warning(f"⚠️ Skipping this article due to error: {inner_e}")
                continue

        logging.info("🔍 No new unpinned tweet found.")

    except Exception as e:
        logging.error(f"❌ Error retrieving tweet: {e}")
        restart_driver()
# --- MAIN LOOP ---
def run_automated_check(username, interval=15):
    try:
        restart_driver()
        while True:
            logging.info("🔍 Checking for latest tweet...")
            get_latest_tweet(username)
            logging.info(f"⏳ Waiting {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("🛑 Stopping script...")
    finally:
        if driver:
            driver.quit()
            logging.info("✅ WebDriver closed")

if __name__ == "__main__":
    run_automated_check(TWITTER_USERNAME, CHECK_INTERVAL)
