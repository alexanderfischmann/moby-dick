import os
import time
import sqlite3
import threading
from dotenv import load_dotenv
from atproto import Client as BskyClient
import tweepy
from flask import Flask, jsonify, request

load_dotenv()

# --- Config (read once, print masked) ---
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE_ENV")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD_ENV")
TARGET_ACCOUNT = os.getenv("TARGET_ACCOUNT_ENV")

TW_CONSUMER_KEY = os.getenv("TW_CONSUMER_KEY_ENV")
TW_CONSUMER_SECRET = os.getenv("TW_CONSUMER_SECRET_ENV")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN_ENV")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET_ENV")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", 120))
DB_PATH = os.getenv("DB_PATH", "posts.db")

def mask(s):
    if not s:
        return "<EMPTY>"
    return s[:3] + "..." + s[-3:]

print("ENV (masked):",
      "BLUESKY_HANDLE=", mask(BLUESKY_HANDLE),
      "TARGET_ACCOUNT=", mask(TARGET_ACCOUNT),
      "TW_KEY=", mask(TW_CONSUMER_KEY),
      "TW_TOKEN=", mask(TW_ACCESS_TOKEN),
      "DB_PATH=", DB_PATH,
      "INTERVAL=", CHECK_INTERVAL)

# --- DB setup ---
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posted (uri TEXT PRIMARY KEY)")
conn.commit()

# --- Initialize clients with try/except so errors show in logs ---
try:
    bluesky = BskyClient()
    bluesky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
    print("✅ Bluesky login OK")
except Exception as e:
    bluesky = None
    print("❌ Bluesky login FAILED:", repr(e))

try:
    twitter = tweepy.Client(
        consumer_key=TW_CONSUMER_KEY,
        consumer_secret=TW_CONSUMER_SECRET,
        access_token=TW_ACCESS_TOKEN,
        access_token_secret=TW_ACCESS_SECRET,
        # wait_on_rate_limit=True  # optional
    )
    # quick sanity check call that doesn't post: get auth user id if possible
    try:
        me = twitter.get_me()
        print("✅ Twitter client OK (get_me returned)", getattr(me, "data", None))
    except Exception as e:
        print("⚠️ Twitter client created but get_me failed:", repr(e))
except Exception as e:
    twitter = None
    print("❌ Failed to create Twitter client:", repr(e))

def check_and_post_latest(dry_run=False):
    """Return dict with status and debug info. dry_run=True won't call Twitter."""
    debug = {"time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    try:
        if not bluesky:
            debug["error"] = "No bluesky client (login failed)."
            print("❌", debug["error"])
            return debug

        # fetch feed
        feed = bluesky.app.bsky.feed.get_author_feed({'actor': TARGET_ACCOUNT, 'limit': 1})
        # defensive extraction
        feed_list = getattr(feed, "feed", None) or getattr(feed, "data", None) or feed
        if not feed_list:
            debug["status"] = "no_posts"
            print("🔍 No posts found for", TARGET_ACCOUNT)
            return debug

        item = feed_list[0]
        post = getattr(item, "post", getattr(item, "value", item))
        uri = getattr(post, "uri", None) or getattr(post, "id", None)
        record = getattr(post, "record", post)
        text = getattr(record, "text", "") or getattr(record, "content", "")
        text = (text or "").strip()

        debug.update({"uri": uri, "text_len": len(text)})

        if not uri:
            debug["status"] = "no_uri"
            print("⚠️ Couldn't determine uri for latest post; debug:", debug)
            return debug

        cur.execute("SELECT uri FROM posted WHERE uri=?", (uri,))
        if cur.fetchone():
            debug["status"] = "already_posted"
            print("ℹ️ Latest post already recorded, skipping. URI:", uri)
            return debug

        if not text:
            debug["status"] = "empty_text"
            # still mark as seen to avoid repost loops
            cur.execute("INSERT OR IGNORE INTO posted (uri) VALUES (?)", (uri,))
            conn.commit()
            print("ℹ️ Latest post has no text; recorded and skipped. URI:", uri)
            return debug

        if len(text) > 280:
            text_to_post = text[:277] + "..."
        else:
            text_to_post = text

        debug["status"] = "will_post" if not dry_run else "dry_run"

        print("🚀 Posting to Twitter (dry_run=%s): %s" % (dry_run, text_to_post[:120]))

        if not dry_run:
            try:
                resp = twitter.create_tweet(text=text_to_post)
                debug["twitter_response"] = getattr(resp, "data", resp)
                # record posted
                cur.execute("INSERT INTO posted (uri) VALUES (?)", (uri,))
                conn.commit()
                debug["status"] = "posted"
                print("✅ Posted to Twitter:", debug["twitter_response"])
            except Exception as e:
                debug["status"] = "twitter_error"
                debug["twitter_error"] = repr(e)
                print("❌ Twitter post FAILED:", repr(e))
        return debug

    except Exception as e:
        debug["status"] = "error"
        debug["error"] = repr(e)
        print("❌ Error in check_and_post_latest:", repr(e))
        return debug

# Background loop
def run_bot_loop():
    print("🤖 Bot loop started — checking every %s seconds" % CHECK_INTERVAL)
    while True:
        result = check_and_post_latest()
        # always flush logs quickly
        time.sleep(CHECK_INTERVAL)

# Flask app with manual trigger
app = Flask(__name__)

@app.route("/")
def index():
    return "🤖 Bluesky → Twitter bot is running", 200

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/run-now", methods=["POST", "GET"])
def run_now():
    """Manually trigger a check. GET shows dry-run; POST actually posts."""
    dry = request.method == "GET"
    result = check_and_post_latest(dry_run=dry)
    return jsonify(result)

# start background thread only when run directly (Render/gunicorn won't call this block)
if __name__ == "__main__":
    thread = threading.Thread(target=run_bot_loop, daemon=True)
    thread.start()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
