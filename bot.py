import os
import time
import sqlite3
import threading
from dotenv import load_dotenv
from atproto import Client
import tweepy
from flask import Flask

load_dotenv()

########### ENV ############

BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE_ENV")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD_ENV")
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT_ENV")

TW_CONSUMER_KEY = os.getenv("TW_CONSUMER_KEY_ENV")
TW_CONSUMER_SECRET = os.getenv("TW_CONSUMER_SECRET_ENV")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN_ENV")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET_ENV")

INTERVAL = 1200  # 20 minutes

########### DB #############

conn = sqlite3.connect('posts.db', check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posted (uri TEXT PRIMARY KEY)")
conn.commit()

########### CLIENTS ########

bluesky = Client()
bluesky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
print("✅ Bluesky login OK")

twitter = tweepy.Client(
    consumer_key=TW_CONSUMER_KEY,
    consumer_secret=TW_CONSUMER_SECRET,
    access_token=TW_ACCESS_TOKEN,
    access_token_secret=TW_ACCESS_SECRET
)
print("✅ Twitter client OK (get_me returned)", twitter.get_me().data.username)

############ BOT ###########

latest_text = "No posts yet."

def check_and_post_latest():
    global latest_text
    try:
        print("\n🔍 Checking Bluesky feed for", TARGET_ACCOUNT)
        feed = bluesky.app.bsky.feed.get_author_feed({'actor': TARGET_ACCOUNT, 'limit': 1})

        if not hasattr(feed, "feed") or not feed.feed:
            print("⚠️ No posts found.")
            return

        post = feed.feed[0].post
        uri = post.uri
        record = getattr(post, "record", None)
        text = getattr(record, "text", "").strip() if record else ""

        print("🆕 Latest post URI:", uri)
        print("🗒️ Bluesky skeet text:", text or "[no text found]")

        # Update global for the Flask page
        latest_text = text or "[No text in latest post]"

        # Check DB to prevent duplicates
        cur.execute("SELECT uri FROM posted WHERE uri=?", (uri,))
        if cur.fetchone():
            print("↩️ Already posted to Twitter.")
            return

        if not text:
            print("⏭️ Skipping — no text to post.")
            return

        # Ensure tweet length
        if len(text) > 280:
            text = text[:277] + "..."

        print("📤 Posting to Twitter:", text)
        twitter.create_tweet(text=text)
        cur.execute("INSERT INTO posted (uri) VALUES (?)", (uri,))
        conn.commit()
        print("✅ Posted new Bluesky update to Twitter.")

    except Exception as e:
        print("❌ Error during check:", e)


def run_loop():
    print(f"🤖 Bot loop started — checking every {INTERVAL} seconds")
    while True:
        check_and_post_latest()
        time.sleep(INTERVAL)


############ FLASK #########

app = Flask(__name__)

@app.route("/")
def index():
    return f"""
    <h1>🤖 Bluesky → Twitter bot is running</h1>
    <p>Latest Bluesky skeet:</p>
    <blockquote>{latest_text}</blockquote>
    """, 200


############ MAIN ##########

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print("Binding Flask to port:", port)
    threading.Thread(target=run_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
