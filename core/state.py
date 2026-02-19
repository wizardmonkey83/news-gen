# weird python concept if you ask me. essentially defines what the agent can remember/be passed

from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    # the topic input for the news story
    topic: str
    num_extensions: Optional[str]

    # fields are optional to avoid errors arisng from empty fields
    # ingestion
    news_summary: Optional[str]
    # i think dict is correct
    sources: dict[str]

    # audio creation
    audio_script: Optional[str]
    audio_length: Optional[float]

    # visuals creation
    visual_script: Optional[str]
    visual_length: Optional[str]

    # storing video, desc in bucket
    storage_prefix: Optional[str]
    reference_image_uri: Optional[str]
    # link to the final video
    video_url: Optional[str]
    
    filename: Optional[str]
    gs_link: Optional[str]

    post_description: Optional[str]

    # list of sites to post to based on user selection
    post_platforms: Optional[list]

    post_urls: Optional[dict]


# feedback state ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class FeedbackState(TypedDict):
    bsky_post_urls: Optional[list]
    post_metrics: Optional[dict]

    post_metric_summary: Optional[str]
    
    dict_video_response: Optional[dict]
    dict_desc_response: Optional[dict]
