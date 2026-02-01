from atproto import Client, AtUri
from config import BSKY_USERNAME, BSKY_PASSWORD

def review_bsky_metrics(bsky_post_urls: list):
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

            at_uri = AtUri.from_str(f"at://{did}/app.bsky.feed.post/{rkey}")
        except Exception as e:
            print(f"Error parsing url: {e}")
            return

        try:
            data = client.get_post_thread(uri=at_uri)
            thread = data.thread

            if not hasattr(thread, "post"):
                print(f"Unable to find post. URL: {url}")
                return
            
            post = data.thread.post
            if hasattr(thread, "replies") and thread.replies:
                for reply in thread.replies:
                    
