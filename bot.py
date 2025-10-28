import time
import sqlite3
from atproto import Client as BskyClient
import tweepy

BLUESKY_HANDLE = "yourname.bsky.social"        # Your Bluesky handle
BLUESKY_PASSWORD = "auv3-vcfh-usq7-rmvb"    # App password (not your main password)
TARGET_ACCOUNT = "targetuser.bsky.social"      # The Bluesky account to mirror

# Twitter API keys (from your developer portal)
TW_CONSUMER_KEY = "VlopdzJOGMISPP4qmGtyGDPOW"
TW_CONSUMER_SECRET = "BiSLWHTxbil8lVjp0oQm98Umze5StmQLmbyfHR3LxXwYJrhBM8"
TW_ACCESS_TOKEN = "1982998290192019456-asp8gvLsX8hSTDcyhj5srWxrVqAI9E"
TW_ACCESS_SECRET = "1982998290192019456-asp8gvLsX8hSTDcyhj5srWxrVqAI9E"