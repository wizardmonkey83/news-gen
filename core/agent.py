from config import DESCRIPTION_PROMPT, PROJECT_ID, LOCAL_DEV
from tools.social import post_to_bsky
from tools.news import collect_news
from tools.video import generate_visuals, loop_image_to_video, generate_did_video
from tools.text import generate_description, generate_text_to_speech_script, generate_visual_script
from tools.notification import send_request
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
    load_prompts_to_config()
    topic, num_extensions = get_topic()

    if LOCAL_DEV:
        num = random.randint(0, 1000)
        storage_prefix = f"{topic}_{num}"
    else:
        storage_prefix = f"{topic}_{date.today()}"
    return {"topic": topic, "num_extensions": num_extensions, "storage_prefix": storage_prefix}

# collects news sources and creates a summary. also creates audio_script
def collect_news_and_summary(state: AgentState):
    result = collect_news(state["topic"])
    news_summary = result["summary"]
    sources = result["sources"]

    audio_script = generate_text_to_speech_script(news_summary, state["num_extensions"])

    return {"news_summary": news_summary, "sources": sources, "audio_script": audio_script}

# saves sources to google sheets
def save_news_sources_to_sheets(state: AgentState):
    sources = state["sources"]
    store_sources(sources)
    # may want to include an interrupt here to allow source editing

# handles audio creation
def create_audio_for_video(state: AgentState):
    audio_length = generate_audio_snippet(state["audio_script"], state["storage_prefix"])
    return {"audio_length": audio_length}

# creates visuals
def create_visual_for_video(state: AgentState):
    # first create visual script
    visual_script = generate_visual_script(state["audio_script"])
    
    # then create visuals
    contents = generate_visuals(visual_script, state["storage_prefix"], state["audio_length"])

    # loop still image
    # contents = loop_image_to_video(state["audio_length"], state["storage_prefix"])

    gs_link = contents["gs_link"]
    visual_length = contents["visuals_length"]
    return {"gs_link": gs_link, "visual_length": visual_length}

    # D-ID gen
    # signed_url = generate_did_video(state["audio_length"], state["storage_prefix"])
    # return {"video_url": signed_url}

# syncs audio and visuals.
def connect_visual_and_audio_for_video(state: AgentState):
    signed_url = sync_visual_and_audio(state["visual_length"], state["audio_length"], state["storage_prefix"])
    return {"video_url": signed_url}

# creates video description
def create_post_description_for_video(state: AgentState):
    gs_link = state["gs_link"]
    post_description = generate_description(gs_link, DESCRIPTION_PROMPT)
    return {"post_description": post_description}

# saves description to bucket
def save_post_description(state: AgentState):
    desc_to_bucket(state["post_description"], state["storage_prefix"])

# sends approve/reject email 
def send_approval_email(state: AgentState, config: RunnableConfig):
    visuals_url = state["video_url"]
    post_description = state["post_description"]
    thread_id = config["configurable"].get("thread_id")
    send_request(visuals_url, post_description, thread_id)

# once video is approved for publishing
def publish_video_and_description(state: AgentState):
    post_url = post_to_bsky(state["post_description"], state["storage_prefix"])
    return {"post_url": post_url}

# marks the topic in the google sheet as complete
def mark_topic_complete(state: AgentState):
    mark_complete(state["post_url"])
    # no need for this :)
    return {"is_complete": True}

graph = StateGraph(AgentState)

client = firestore.Client(project=PROJECT_ID)
memory = FirestoreSaver(project_id=PROJECT_ID)
# thread_id is the slot the state is saved to
config = {"configurable": {"thread_id": f"2026-02-06_test_211313565321"}}

graph.add_node("load_prompts_and_get_topic", load_prompts_and_get_topic)
graph.add_node("collect_news_and_summary", collect_news_and_summary)
graph.add_node("save_news_sources_to_sheets", save_news_sources_to_sheets)
graph.add_node("create_audio_for_video", create_audio_for_video)
graph.add_node("create_visual_for_video", create_visual_for_video)
graph.add_node("connect_visual_and_audio_for_video", connect_visual_and_audio_for_video)
graph.add_node("create_post_description_for_video", create_post_description_for_video)
graph.add_node("save_post_description", save_post_description)
graph.add_node("send_approval_email", send_approval_email)
graph.add_node("publish_video_and_description", publish_video_and_description)
graph.add_node("mark_topic_complete", mark_topic_complete)

graph.add_edge(START, "load_prompts_and_get_topic")
graph.add_edge("load_prompts_and_get_topic", "collect_news_and_summary")
graph.add_edge("collect_news_and_summary", "save_news_sources_to_sheets")
graph.add_edge("save_news_sources_to_sheets", "create_audio_for_video")
graph.add_edge("create_audio_for_video", "create_visual_for_video")
graph.add_edge("create_visual_for_video", "connect_visual_and_audio_for_video")
graph.add_edge("connect_visual_and_audio_for_video", "create_post_description_for_video")
graph.add_edge("create_post_description_for_video", "save_post_description")
graph.add_edge("save_post_description", "send_approval_email")
graph.add_edge("send_approval_email", "publish_video_and_description")
graph.add_edge("publish_video_and_description", "mark_topic_complete")
graph.add_edge("mark_topic_complete", END)

# run command
app = graph.compile(interrupt_before=["publish_video_and_description"], checkpointer=memory)

if __name__ == "__main__":
    snapshot = app.get_state(config)
    if snapshot.next:
        # if the agent was paused it will resume where it left off
        app.invoke(None, config=config)
    else:
        # how to pass state?
        app.invoke({"is_complete": False}, config=config)