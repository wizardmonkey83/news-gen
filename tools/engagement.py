from atproto import Client, AtUri
from config import BSKY_USERNAME, BSKY_PASSWORD

def bsky_metrics(post_url):
    client = Client()
    client.login(BSKY_USERNAME, BSKY_PASSWORD)
    
