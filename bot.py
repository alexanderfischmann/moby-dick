import time
import sqlite3
from atproto import Client as BskyClient
import tweepy

BLUESKY_HANDLE = "thealexsylvian.bsky.social"
BLUESKY_PASSWORD = "auv3-vcfh-usq7-rmvb"
TARGET_ACCOUNT = "mobydickatsea.bsky.social"

TW_CONSUMER_KEY = "VlopdzJOGMISPP4qmGtyGDPOW"
TW_CONSUMER_SECRET = "BiSLWHTxbil8lVjp0oQm98Umze5StmQLmbyfHR3LxXwYJrhBM8"
TW_ACCESS_TOKEN = "1982998290192019456-asp8gvLsX8hSTDcyhj5srWxrVqAI9E"
TW_ACCESS_SECRET = "1982998290192019456-asp8gvLsX8hSTDcyhj5srWxrVqAI9E"

##########

conn = sqlite3.connect('posts.db')
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posted (uri TEXT PRIMARY KEY)")
conn.commit()

######

bsky = BskyClient()
bsky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)

###########

twitter = tweepy.Client(
    consumer_key=TW_CONSUMER_KEY,
    consumer_secret=TW_CONSUMER_SECRET,
    access_token=TW_ACCESS_TOKEN,
    access_token_secret=TW_ACCESS_SECRET
)

###########

def check_and_post_latest():
    try:
        feed = bsky.app.bsky.feed.get_author_feed({'actor': TARGET_ACCOUNT, 'limit': 1})
        if not feed['feed']:
            print("No posts found.")
            return

        post = feed['feed'][0]['post']
        uri = post['uri']
        text = post['record'].get('text', '').strip()

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

# ---- LOOP ----
print("🤖 Bot started! Checking every 2 minutes...")
while True:
    check_and_post_latest()
    time.sleep(120)