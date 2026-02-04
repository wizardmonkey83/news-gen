from atproto import Client
from config import BSKY_USERNAME, BSKY_PASSWORD, MOCK_BSKY_METRICS, PROJECT_ID, LOCATION, TEXT_MODEL, SUMMARIZE_RAW_POST_METRICS_PROMPT
from datetime import datetime
import time
import json
from atproto_client.models.app.bsky.feed.defs import ThreadViewPost, BlockedPost, NotFoundPost

from google.cloud import firestore
from google import genai
from google.genai import types

def extract_bsky_replies(thread: str):
    # from atproto docs. could not be more confusing
    if not isinstance(thread, ThreadViewPost):
        return None

    post = thread.post
    scraped_at  = str(datetime.now())

    post_metrics = {
        "uri": post.uri,
        "author_handle": post.author.handle,
        "text": post.record.text,
        "posted_at": post.indexed_at,
        "scraped_at": scraped_at,
        "metrics": {
            "likes": post.like_count or 0,
            "reposts": post.repost_count or 0,
            "replies": post.reply_count or 0,
        },
        "replies": [],
    }

    if thread.replies:
        for reply in thread.replies:
            processed_reply = extract_bsky_replies(reply)
            if processed_reply:
                post_metrics["replies"].append(processed_reply)

    return post_metrics
            

def extract_bsky_metrics(bsky_post_urls: list):
    if not MOCK_BSKY_METRICS:
        print("!!REAL!! PARSING BSKY URLS...")
        client = Client()
        client.login(BSKY_USERNAME, BSKY_PASSWORD)

        metrics = {}
        for url in bsky_post_urls:
            try:
                parts = url.split("/")
                if "profile" not in parts or "post" not in parts:
                    raise ValueError("Invalid bsky url format")
                
                handle_index, post_index = parts.index("profile") + 1, parts.index("post") + 1
                handle, rkey = parts[handle_index], parts[post_index]

                doc = client.resolve_handle(handle)
                did = doc.did

                at_uri = f"at://{did}/app.bsky.feed.post/{rkey}"
            except Exception as e:
                print(f"Error parsing url: {e}")
                continue
            
            try:
                data = client.get_post_thread(uri=at_uri, depth=1000, parent_height=0)
                thread = data.thread

                if not isinstance(thread, ThreadViewPost):
                    print(f"Unable to find post. URL: {url}")
                    continue

                post_metrics = extract_bsky_replies(thread)

                if post_metrics:
                    post_metrics["url"] = url
                    metrics["metrics"] = post_metrics

            except Exception as e:
                print(f"Error occured: {e}")
                continue

            time.sleep(1)

        print(f"!!REAL!! POST METRICS GATHERED: {metrics}")
        return metrics

    else:

        post_metrics = {
            "uri": "at:did:plc:1234",
            "author_handle": "mickey mouse",
            "text": "post about clubhouses",
            "posted_at": "01/01/0001",
            "scraped_at": "02/03/2026",
            "metrics": {
                "likes": 50,
                "reposts": 3,
                "replies": 2,
            },
            "replies": [
                {"text": "this post is so bad. sesame street rules."},
                {"text": "the voice speaks way too fast. kinda hard to understand."},
                {"text": "the lighting is too dark, looks depressing."}
            ],
            "url": "https://fake_url.com"
        }

        return post_metrics
    
# formats/summarizes the post_metrics into a human friendly format -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def summarize_bsky_metrics(post_metrics: dict):
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

    response = client.model.generate_description(
        model=TEXT_MODEL,
        contents=[SUMMARIZE_RAW_POST_METRICS_PROMPT, json.dumps(post_metrics)]
    )

    post_metric_summary = response.text

    return post_metric_summary