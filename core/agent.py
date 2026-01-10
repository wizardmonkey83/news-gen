from config import TEXT_MODEL, SYSTEM_PROMPT, TOPIC
from tools.social import post_tweet
from tools.news import collect_news
from tools.video import generate_video
from state import AgentState

from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langgraph.graph import StateGraph, START, END

model = init_chat_model(
    TEXT_MODEL,
    # how creative responses are. higher is more creative/varied
    temperature=0.0
)

def configure():
    # this works......?
    return {"topic": AgentState["topic"] + TOPIC, "is_complete": AgentState["is_complete"] + False}

def editor(state: AgentState):
    result = collect_news(TOPIC)
    news_summary = result[0]
    sources = result[1]
    return {"news_summary": AgentState["news_summary"] + news_summary, "sources": AgentState["sources"] + sources}

def director(state: AgentState):
    video_url = generate_video(SYSTEM_PROMPT, TOPIC)
    return {"video_url": AgentState["video_url"] + video_url}

# THERE NEEDS TO BE HUMAN INTERVENTION HERE. AN EMAIL SHOULD BE SENT CONTAINING THE VIDEO AND DESCRIPTION TO BE APPROVED.

# once video is approved for publishing
def publisher(state: AgentState):
    # placeholder
    return None

graph = StateGraph(AgentState)
graph.add_node("configure", configure)
graph.add_node("editor", editor)
graph.add_node("director", director)
graph.add_node("publisher", publisher)
graph.add_edge(START, "configure")
graph.add_edge("publisher", END)










