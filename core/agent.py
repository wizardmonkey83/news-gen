from config import TEXT_MODEL, SYSTEM_PROMPT, TOPIC, VIDEO_PROMPT
from tools.social import post_tweet
from tools.news import collect_news
from tools.video import generate_video
from state import AgentState

from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langgraph.graph import StateGraph, START, END

from google import genai

model = init_chat_model(
    TEXT_MODEL,
    # how creative responses are. higher is more creative/varied
    temperature=0.0
)

def configure(state: AgentState):
    # this works......?
    return {"topic": TOPIC, "is_complete": False}

def editor(state: AgentState):
    result = collect_news(TOPIC)
    news_summary = result["summary"]
    sources = result["sources"]
    return {"news_summary": news_summary, "sources": sources}

def director(state: AgentState):
    # i think this is sufficient. theres not really a need to make a gemini call here
    prompt = f"Create a detailed video on this topic: {TOPIC}. Use this for generation guidelines: {VIDEO_PROMPT}"
    video_url = generate_video(prompt, TOPIC)
    return {"video_url": video_url}

# THERE NEEDS TO BE HUMAN INTERVENTION HERE. AN EMAIL SHOULD BE SENT CONTAINING THE VIDEO AND DESCRIPTION TO BE APPROVED.

# once video is approved for publishing
def publisher(state: AgentState):
    # placeholder
    # remember to toggle is_complete to true here
    return None

graph = StateGraph(AgentState)
graph.add_node("configure", configure)
graph.add_node("editor", editor)
graph.add_node("director", director)
graph.add_node("publisher", publisher)

graph.add_edge(START, "configure")
graph.add_edge("configure", "editor")
graph.add_edge("editor", "director")
graph.add_edge("director", "publisher")
graph.add_edge("publisher", END)

# run command
app = graph.compile(interrupt_before=["publisher"])










