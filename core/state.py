# weird python concept if you ask me. essentially defines what the agent can remember/be passed

from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    # the topic input for the news story
    topic: str

    # fields are optional to avoid errors arisng from empty fields
    # ingestion
    news_summary: Optional[str]
    # i think dict is correct
    source: dict[str]

    # creation
    script: Optional[str]
    video_prompt: Optional[str]
    # link to the final video
    video_url: Optional[str]
    gs_link: Optional[str]
    post_description: Optional[str]

    # status tracking
    is_complete: bool
    error: Optional[str]