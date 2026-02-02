from core.state import AnalystState
from tools.sheets import get_bsky_url
from tools.engagement import extract_bsky_metrics
from tools.sentiment import review_bsky_metrics
from tools.storage import bsky_metrics_to_firestore

def starter(state: AnalystState):
    bsky_post_urls = get_bsky_url()
    return {"bsky_post_urls": bsky_post_urls}

# extracts metrics/engagement from post 
def extracter(state: AnalystState):
    metrics = extract_bsky_metrics(state["bsky_post_urls"])
    return {"post_metrics": metrics}

# saves post_metrics as a json file in a gs bucket
def converter(state: AnalystState):
    bsky_metrics_to_firestore(state["post_metrics"])

# compares metrics to current prompt/s
def reviewer(state: AnalystState):
    contents = review_bsky_metrics(state["post_metrics"])
    return {
        "json_video_response": contents["json_video_response"], 
        "json_desc_response": contents["json_desc_response"],
    }

def updater(state: AnalystState):
    