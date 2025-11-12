import os
import time
import sqlite3
import threading
from dotenv import load_dotenv
from atproto import Client
import tweepy
from flask import Flask, render_template_string

load_dotenv()

# --- ENV ---
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT")

TW_CONSUMER_KEY = os.getenv("TW_CONSUMER_KEY")
TW_CONSUMER_SECRET = os.getenv("TW_CONSUMER_SECRET")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET")

INTERVAL = int(os.getenv("INTERVAL", 120))

# --- DB ---
conn = sqlite3.connect('posts.db', check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posted (uri TEXT PRIMARY KEY, text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
conn.commit()

# --- Clients ---
bluesky = Client()
bluesky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)

twitter = tweepy.Client(
    consumer_key=TW_CONSUMER_KEY,
    consumer_secret=TW_CONSUMER_SECRET,
    access_token=TW_ACCESS_TOKEN,
    access_token_secret=TW_ACCESS_SECRET
)

print("✅ Bluesky login OK")
print("✅ Twitter client OK (get_me returned)", twitter.get_me().data.username)

# --- Flask app ---
app = Flask(__name__)

# --- Bot function ---
def check_and_post_latest():
    while True:
        try:
            print(f"🔍 Checking Bluesky feed for {TARGET_ACCOUNT}")
            feed = bluesky.app.bsky.feed.get_author_feed({'actor': TARGET_ACCOUNT, 'limit': 1})
            if not feed.feed:
                print("No posts found.")
            else:
                post = feed.feed[0].post
                uri = post.uri
                text = getattr(post.record, "text", "").strip()
                print("Latest Bluesky post text:", text)

                cur.execute("SELECT uri FROM posted WHERE uri=?", (uri,))
                if not cur.fetchone() and text:
                    # truncate if too long for Twitter
                    tweet_text = text if len(text) <= 280 else text[:277] + "..."
                    twitter.create_tweet(text=tweet_text)
                    cur.execute("INSERT INTO posted (uri, text) VALUES (?, ?)", (uri, text))
                    conn.commit()
                    print("✅ Posted new Bluesky update to Twitter:", tweet_text)
                else:
                    print("No new post to post to Twitter.")
        except Exception as e:
            print("❌ Error:", e)

        time.sleep(INTERVAL)

# --- Dashboard ---
@app.route("/")
def index():
    cur.execute("SELECT text, timestamp FROM posted ORDER BY timestamp DESC LIMIT 10")
    posts = cur.fetchall()
    html = """
    <h1>🤖 Bluesky → Twitter Bot Dashboard</h1>
    <ul>
    {% for text, timestamp in posts %}
        <li><strong>{{ timestamp }}:</strong> {{ text }}</li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, posts=posts)

# --- Run bot in background thread ---
threading.Thread(target=check_and_post_latest, daemon=True).start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
