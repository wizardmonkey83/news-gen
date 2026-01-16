from config import VIDEO_PROMPT, DESCRIPTION_PROMPT, PROJECT_ID
from tools.social import post_tweet
from tools.news import collect_news
from tools.video import generate_video, generate_description
from tools.notification import send_request
from tools.sheets import get_topic
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

def director(state: AgentState):
    # i think this is sufficient. theres not really a need to make a gemini call here
    prompt = f"Create a detailed video on this topic: {state["topic"]}. Use this for generation guidelines: {VIDEO_PROMPT}"
    contents = generate_video(prompt, state["topic"])
    video_url = contents["gs_link"]
    filename = contents["filename"]

    post_description = generate_description(video_url, DESCRIPTION_PROMPT, filename)
    return {"video_url": video_url, "post_description": post_description}

def notifier(state: AgentState, config: RunnableConfig):
    video_url = state["video_url"]
    post_description = state["post_description"]
    thread_id = config["configurable"].get("thread_id")
    # not super sure how to call this
    send_request(video_url, post_description, thread_id)

# once video is approved for publishing
def publisher(state: AgentState):
    # placeholder
    print("PUBLISHING MOCK TWEET....")
    return {"is_complete": True}

graph = StateGraph(AgentState)

client = firestore.Client(project=PROJECT_ID)
memory = FirestoreSaver(project_id=PROJECT_ID)
# thread_id is the slot the state is saved to
config = {"configurable": {"thread_id": f"{date.today()}"}}

graph.add_node("starter", starter)
graph.add_node("editor", editor)
graph.add_node("director", director)
graph.add_node("notifier", notifier)
graph.add_node("publisher", publisher)

graph.add_edge(START, "starter")
graph.add_edge("starter", "editor")
graph.add_edge("editor", "director")
graph.add_edge("director", "notifier")
graph.add_edge("notifier", "publisher")
graph.add_edge("publisher", END)

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










