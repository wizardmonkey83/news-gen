from config import VIDEO_PROMPT, DESCRIPTION_PROMPT, PROJECT_ID, LOCAL_DEV
from tools.social import post_to_bsky
from tools.news import collect_news
from tools.video import generate_video, generate_description
from tools.notification import send_request
from tools.sheets import get_topic, mark_complete, store_sources
from tools.storage import desc_to_bucket
from core.state import AgentState

from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph_checkpoint_firestore import FirestoreSaver
from google.cloud import firestore
from langgraph.graph import StateGraph, START, END
from google import genai
from datetime import date
import random

# gets topic from google sheet
def starter(state: AgentState):
    print("WAKING UP....")
    topic = get_topic()
    if LOCAL_DEV:
        num = random.randint(0, 1000)
        storage_prefix = f"{topic}_{num}"
    else:
        storage_prefix = f"{topic}_{date.today()}"
    return {"topic": topic, "storage_prefix": storage_prefix}

# collects news sources and creates a summary
def editor(state: AgentState):
    result = collect_news(state["topic"])
    news_summary = result["summary"]
    sources = result["sources"]

    return {"news_summary": news_summary, "sources": sources}

# saves sources to google sheets
def archiver(state: AgentState):
    sources = state["sources"]
    store_sources(sources)
    # may want to include an interrupt here to allow source editing

# creates video
def director(state: AgentState):
    # i think this is sufficient. theres not really a need to make a gemini call here
    prompt = f"""
        Create a detailed video on this topic: {state["topic"]}. This is a summary of news gathered on the topic, use it for context: {state["news_summary"]} 
        Use this for generation guidelines: {VIDEO_PROMPT}
    """
    
    contents = generate_video(prompt, state["storage_prefix"])
    gs_link = contents["gs_link"]
    video_url = contents["video_url"]

    return {"video_url": video_url, "gs_link": gs_link}

# creates video description
def writer(state: AgentState):
    gs_link = state["gs_link"]
    post_description = generate_description(gs_link, DESCRIPTION_PROMPT)
    return {"post_description": post_description}

# saves video and post description to newly created google drive folder
def saver(state: AgentState):
    desc_to_bucket(state["post_description"], state["storage_prefix"])

# sends approve/reject email 
def notifier(state: AgentState, config: RunnableConfig):
    video_url = state["video_url"]
    post_description = state["post_description"]
    thread_id = config["configurable"].get("thread_id")
    send_request(video_url, post_description, thread_id)

# once video is approved for publishing
def publisher(state: AgentState):
    post_to_bsky(state["post_description"], state["storage_prefix"])

# marks the topic in the google sheet as complete
def cleaner(state: AgentState):
    mark_complete()
    # no need for this 
    return {"is_complete": True}

graph = StateGraph(AgentState)

client = firestore.Client(project=PROJECT_ID)
memory = FirestoreSaver(project_id=PROJECT_ID)
# thread_id is the slot the state is saved to
config = {"configurable": {"thread_id": f"2026-01-29+test2344321"}}

graph.add_node("starter", starter)
graph.add_node("editor", editor)
graph.add_node("archiver", archiver)
graph.add_node("director", director)
graph.add_node("writer", writer)
graph.add_node("saver", saver)
graph.add_node("notifier", notifier)
graph.add_node("publisher", publisher)
graph.add_node("cleaner", cleaner)

graph.add_edge(START, "starter")
graph.add_edge("starter", "editor")
graph.add_edge("editor", "archiver")
graph.add_edge("archiver", "director")
graph.add_edge("director", "writer")
graph.add_edge("writer", "saver")
graph.add_edge("saver", "notifier")
graph.add_edge("notifier", "publisher")
graph.add_edge("publisher", "cleaner")
graph.add_edge("cleaner", END)

# run command
app = graph.compile(interrupt_before=["publisher"], checkpointer=memory)

if __name__ == "__main__":
    snapshot = app.get_state(config)
    if snapshot.next:
        # if the agent was paused it will resume where it left off
        app.invoke(None, config=config)
    else:
        # how to pass state?
        app.invoke({"is_complete": False}, config=config)