import requests
from config import MOCK_SOCIAL

def post_tweet(description: str, video_uri: str):
    if not MOCK_SOCIAL:
        url = "https://api.x.com/2/tweets"

        payload = {
            "card_uri": "<string>",
            "community_id": "1146654567674912769",
            "direct_message_deep_link": "<string>",
            "edit_options": { "previous_post_id": "1346889436626259968" },
            "for_super_followers_only": False,
            "geo": { "place_id": "<string>" },
            "media": {
                "media_ids": ["1146654567674912769"],
                "tagged_user_ids": ["2244994945"]
            },
            "nullcast": False,
            "poll": {
                "duration_minutes": 5042,
                "options": ["<string>"],
                "reply_settings": "following"
            },
            "quote_tweet_id": "1346889436626259968",
            "reply": {
                "in_reply_to_tweet_id": "1346889436626259968",
                "auto_populate_reply_metadata": True,
                "exclude_reply_user_ids": ["2244994945"]
            },
            "reply_settings": "following",
            "share_with_followers": False,
            "text": "Learn how to use the user Tweet timeline and user mention timeline endpoints in the X API v2 to explore Tweet\u2026 https:\/\/t.co\/56a0vZUx7i"
        }
        headers = {
            "Authorization": "Bearer <token>",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
    else:
        # to avoid setting up a twitter dev account
        print(f"Description: {description}")
        print(f"Video URI: {video_uri}")
        return "https://twitter.com/fake/status/123"