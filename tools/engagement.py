from atproto import Client, AtUri
from config import BSKY_USERNAME, BSKY_PASSWORD
from datetime import datetime
import time
from atproto_client.models.app.bsky.feed.defs import ThreadViewPost, BlockedPost, NotFoundPost

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
            

def review_bsky_metrics(bsky_post_urls: list):
    client = Client()
    client.login(BSKY_USERNAME, BSKY_PASSWORD)

    metrics = []
    for url in bsky_post_urls:
        try:
            parts = url.split("/")
            if "profile" not in parts or "post" not in parts:
                raise ValueError("Invalid bsky url format")
            
            handle_index, post_index = parts.index("profile") + 1, parts.index("post") + 1
            handle, rkey = parts[handle_index], parts[post_index]

            doc = client.resolve_handle(handle)
            did = doc.did

            at_uri = AtUri.from_str(f"at://{did}/app.bsky.feed.post/{rkey}")
        except Exception as e:
            print(f"Error parsing url: {e}")
            continue
        
        try:
            data = client.get_post_thread(uri=at_uri, depth=1000, parent_height=0)
            thread = data.thread

            if not isinstance(thread, ThreadViewPost):
                print(f"Unable to find post. URL: {url}")
                continue

            post_metrics = extract_bsky_replies(thread, url)

            if post_metrics:
                post_metrics["url"] = url
                metrics.append(post_metrics)

        except Exception as e:
            print(f"Error occured: {e}")
            continue

        time.sleep(1)
    return metrics