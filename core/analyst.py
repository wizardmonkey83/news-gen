from core.state import AnalystState
from tools.sheets import get_bsky_url
from tools.engagement import review_bsky_metrics

def starter(state: AnalystState):
    bsky_post_urls = get_bsky_url()
    return {"bsky_post_urls": bsky_post_urls}

def reviewer(state: AnalystState):
    review_bsky_metrics(state["bsky_post_urls"])