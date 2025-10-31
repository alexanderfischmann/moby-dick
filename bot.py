import os
import time
import sqlite3
from dotenv import load_dotenv
from atproto import Client
import tweepy

load_dotenv()

###########

BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE_ENV")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD_ENV")
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT_ENV")

TW_CONSUMER_KEY = os.getenv("TW_CONSUMER_KEY_ENV")
TW_CONSUMER_SECRET = os.getenv("TW_CONSUMER_SECRET_ENV")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN_ENV")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET_ENV")

###########

conn = sqlite3.connect('posts.db')
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posted (uri TEXT PRIMARY KEY)")
conn.commit()

bluesky = Client()
bluesky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)

twitter = tweepy.Client(
    consumer_key=TW_CONSUMER_KEY,
    consumer_secret=TW_CONSUMER_SECRET,
    access_token=TW_ACCESS_TOKEN,
    access_token_secret=TW_ACCESS_SECRET
)

############

def check_and_post_latest():
    try:
        feed = bluesky.app.bsky.feed.get_author_feed({'actor': TARGET_ACCOUNT, 'limit': 1})
        if not feed.feed:
            print("No posts found.")
            return

        post = feed.feed[0].post
        uri = post.uri
        text = getattr(post.record, "text", "").strip()

        cur.execute("SELECT uri FROM posted WHERE uri=?", (uri,))
        if cur.fetchone():
            print("No new post yet.")
            return

        if not text:
            print("Latest post has no text.")
            return

        if len(text) > 280:
            text = text[:277] + "..."

        twitter.create_tweet(text=text)
        cur.execute("INSERT INTO posted (uri) VALUES (?)", (uri,))
        conn.commit()
        print("✅ Posted new Bluesky update to Twitter:", text)

    except Exception as e:
        print("❌ Error:", e)

# ---- Loop ----
print("🤖 Bot started! Checking every 2 minutes...")
while True:
    check_and_post_latest()
    time.sleep(120)


# if __name__ == "__main__":
#     print("🤖 Bot started!")
#     check_and_post_latest()

