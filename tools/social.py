from atproto import Client
from config import MOCK_SOCIAL, BSKY_USERNAME, BSKY_PASSWORD

def post_tweet(description: str, video_uri: str):
    if not MOCK_SOCIAL:
        client = Client()
        client.login(BSKY_USERNAME, BSKY_PASSWORD)

        post = client.send_post()