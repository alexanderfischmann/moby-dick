from dotenv import load_dotenv
from atproto import Client
import os

load_dotenv()

print("HELLO")

bluesky = Client()
bluesky.login(os.getenv("BLUESKY_HANDLE_ENV"), os.getenv("BLUESKY_PASSWORD_ENV"))
print("✅ Bluesky login successful!")