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