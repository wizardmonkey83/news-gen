from config import VIDEO_PROMPT, DESCRIPTION_PROMPT, PROJECT_ID
from tools.social import post_tweet
from tools.news import collect_news
from tools.video import generate_video, generate_description
from tools.notification import send_request
from tools.sheets import get_topic, mark_complete, store_sources
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

def starter(state: AgentState):
    print("WAKING UP....")
    topic = get_topic()
    return {"topic": topic}

def editor(state: AgentState):
    result = collect_news(state["topic"])
    news_summary = result["summary"]
    sources = result["sources"]

    return {"news_summary": news_summary, "sources": sources}

def archiver(state: AgentState):
    sources = state["sources"]
    store_sources(sources)
    # may want to include an interrupt here to allow source editing

def director(state: AgentState):
    # i think this is sufficient. theres not really a need to make a gemini call here
    prompt = f"""
        Create a detailed video on this topic: {state["topic"]}. This is a summary of news gathered on the topic, use it for context: {state["news_summary"]} 
        Use this for generation guidelines: {VIDEO_PROMPT}
    """
    
    contents = generate_video(prompt, state["topic"])
    gs_link = contents["gs_link"]
    video_url = contents["video_url"]

    return {"video_url": video_url, "gs_link": gs_link}

def writer(state: AgentState):
    gs_link = state["gs_link"]
    post_description = generate_description(gs_link, DESCRIPTION_PROMPT)
    return {"post_description": post_description}

def notifier(state: AgentState, config: RunnableConfig):
    video_url = state["video_url"]
    post_description = state["post_description"]
    thread_id = config["configurable"].get("thread_id")
    send_request(video_url, post_description, thread_id)

# once video is approved for publishing
def publisher(state: AgentState):
    # placeholder for post_tweet
    print("PUBLISHING MOCK TWEET....")
    return {"is_complete": True}

def cleaner(state: AgentState):
    mark_complete()

graph = StateGraph(AgentState)

client = firestore.Client(project=PROJECT_ID)
memory = FirestoreSaver(project_id=PROJECT_ID)
# thread_id is the slot the state is saved to
config = {"configurable": {"thread_id": f"{date.today()}+test12319653"}}

graph.add_node("starter", starter)
graph.add_node("editor", editor)
graph.add_node("archiver", archiver)
graph.add_node("director", director)
graph.add_node("writer", writer)
graph.add_node("notifier", notifier)
graph.add_node("publisher", publisher)
graph.add_node("cleaner", cleaner)

graph.add_edge(START, "starter")
graph.add_edge("starter", "editor")
graph.add_edge("editor", "archiver")
graph.add_edge("archiver", "director")
graph.add_edge("director", "writer")
graph.add_edge("writer", "notifier")
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










