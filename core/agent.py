from config import DESCRIPTION_PROMPT, PROJECT_ID, LOCAL_DEV, DEMO
from tools.social import post_to_bsky
from tools.news import collect_rss_sources_for_review, filter_selected_rss_sources
from tools.video import generate_visuals
from tools.text import generate_description, generate_text_to_speech_script, generate_rss_summary
from tools.audio import generate_audio_snippet
from tools.sheets import get_topic, mark_complete, store_sources
from tools.sync import sync_visual_and_audio
from tools.storage import desc_to_bucket, load_prompts_to_config
from core.state import AgentState

from langchain_core.runnables import RunnableConfig
from langgraph_checkpoint_firestore import FirestoreSaver
from google.cloud import firestore
from langgraph.graph import StateGraph, START, END
from datetime import date
import random

# gets topic from google sheet
def load_prompts_and_get_topic(state: AgentState):
    print("WAKING UP....")
    if not DEMO:
        load_prompts_to_config()
        topic, num_extensions = get_topic()

        if LOCAL_DEV:
            num = random.randint(0, 1000)
            storage_prefix = f"{topic}_{num}"
        else:
            storage_prefix = f"{topic}_{date.today()}"
        return {"topic": topic, "num_extensions": num_extensions, "storage_prefix": storage_prefix}
    else:
        topic = state.get("topic", "")
        if LOCAL_DEV:
             num = random.randint(0, 1000)
             storage_prefix = f"{topic}_{num}"
        else:
             storage_prefix = f"{topic}_{date.today()}"
        return {"storage_prefix": storage_prefix, "topic": topic}

# collects news sources to display for approval
def collect_sources_for_review(state: AgentState):
    sources, rss_feed_response = collect_rss_sources_for_review(topic=state["topic"])

    return {"rss_feed_response": rss_feed_response, "neat_rss_sources": sources}

# saves selected sources, generates audioo script to be approved
def save_sources_create_audio_script(state: AgentState):
    filtered_sources = filter_selected_rss_sources(approved_sources=state.get("selected_sources"), rss_feed_response=state["rss_feed_response"])

    news_summary = generate_rss_summary(filtered_sources)

    target_length = state.get("target_length", 8)
    audio_script = generate_text_to_speech_script(news_summary=news_summary, target_length=target_length)

    return {"news_summary": news_summary, "audio_script": audio_script}

# saves sources to google sheets
def save_news_sources_to_sheets(state: AgentState):
    sources = state.get("selected_sources", {})
    store_sources(sources)

# handles audio creation
def create_audio_for_video(state: AgentState):
    audio_length = generate_audio_snippet(audio_script=state["audio_script"], storage_prefix=state["storage_prefix"])
    return {"audio_length": audio_length}

# creates visuals
def create_visual_for_video(state: AgentState):
    # then create visuals
    contents = generate_visuals(selected_anchor=state.get("selected_anchor", "anchor_1.png"), storage_prefix=state["storage_prefix"], audio_length=state["audio_length"])

    gs_link = contents["gs_link"]
    visual_length = contents["visuals_length"]
    return {"gs_link": gs_link, "visual_length": visual_length}

# syncs audio and visuals.
def connect_visual_and_audio_for_video(state: AgentState):
    signed_url = sync_visual_and_audio(visual_length=state["visual_length"], audio_length=state["audio_length"], storage_prefix=state["storage_prefix"])
    return {"video_url": signed_url}

# creates video description
def create_post_description_for_video(state: AgentState):
    gs_link = state["gs_link"]
    post_description = generate_description(prompt=DESCRIPTION_PROMPT, news_summary=state["news_summary"])
    return {"post_description": post_description}

# saves description to bucket
def save_post_description(state: AgentState):
    desc_to_bucket(description=state["post_description"], storage_prefix=state["storage_prefix"])

# once video is approved for publishing
def publish_video_and_description(state: AgentState):
    if state.get("post_platforms", []):
        post_urls = {}
        for site in state["post_platforms"]:
            if site == "bsky":
                bsky_post_url = post_to_bsky(description=state["post_description"], storage_prefix=state["storage_prefix"])
                post_urls["bsky_post_url"] = bsky_post_url
            # more sites to come
    
        return {"post_urls": post_urls}
    else:
        return None

# marks the topic in the google sheet as complete
def mark_topic_complete(state: AgentState):
    if not DEMO:
        mark_complete(state.get("post_urls", []))
    return None

graph = StateGraph(AgentState)

client = firestore.Client(project=PROJECT_ID)
memory = FirestoreSaver(project_id=PROJECT_ID)
config = {"configurable": {"thread_id": f"demo-suit-test-1292444732199429"}}

graph.add_node("load_prompts_and_get_topic", load_prompts_and_get_topic)
graph.add_node("collect_sources_for_review", collect_sources_for_review)
graph.add_node("save_sources_create_audio_script", save_sources_create_audio_script)
graph.add_node("save_news_sources_to_sheets", save_news_sources_to_sheets)
graph.add_node("create_audio_for_video", create_audio_for_video)
graph.add_node("create_visual_for_video", create_visual_for_video)
graph.add_node("connect_visual_and_audio_for_video", connect_visual_and_audio_for_video)
graph.add_node("create_post_description_for_video", create_post_description_for_video)
graph.add_node("save_post_description", save_post_description)
graph.add_node("publish_video_and_description", publish_video_and_description)
graph.add_node("mark_topic_complete", mark_topic_complete)

graph.add_edge(START, "load_prompts_and_get_topic")
graph.add_edge("load_prompts_and_get_topic", "collect_sources_for_review")
graph.add_edge("collect_sources_for_review", "save_sources_create_audio_script")
graph.add_edge("save_sources_create_audio_script", "save_news_sources_to_sheets")
graph.add_edge("save_news_sources_to_sheets", "create_audio_for_video")
graph.add_edge("create_audio_for_video", "create_visual_for_video")
graph.add_edge("create_visual_for_video", "connect_visual_and_audio_for_video")
graph.add_edge("connect_visual_and_audio_for_video", "create_post_description_for_video")
graph.add_edge("create_post_description_for_video", "save_post_description")
graph.add_edge("save_post_description", "publish_video_and_description")
graph.add_edge("publish_video_and_description", "mark_topic_complete")
graph.add_edge("mark_topic_complete", END)

app = graph.compile(interrupt_before=["save_sources_create_audio_script", "save_news_sources_to_sheets", "publish_video_and_description"], checkpointer=memory)

if __name__ == "__main__":
    snapshot = app.get_state(config)
    if snapshot.next:
        # if the agent was paused it will resume where it left off
        app.invoke(None, config=config)
    else:
        app.invoke(None, config=config)