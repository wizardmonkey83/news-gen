from core.state import FeedbackState
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph_checkpoint_firestore import FirestoreSaver
from google.cloud import firestore
from config import PROJECT_ID, DEMO
import random
from datetime import date


from tools.sheets import get_bsky_url
from tools.engagement import extract_bsky_metrics, summarize_bsky_metrics
from tools.sentiment import review_bsky_metrics
from tools.staging import stage_prompts_for_review
from tools.storage import bsky_metrics_to_firestore, bsky_prompt_changes_to_firestore


def starter(state: FeedbackState):
    if not state.get("bsky_post_urls"):
        bsky_post_urls = get_bsky_url()
        return {"bsky_post_urls": bsky_post_urls}
    
    else: 
        return {}

# extracts metrics/engagement from post 
def extracter(state: FeedbackState):
    post_metrics = extract_bsky_metrics(state["bsky_post_urls"])
    post_metric_summary = summarize_bsky_metrics(post_metrics)
    return {"post_metrics": post_metrics, "post_metric_summary": post_metric_summary}

# saves post_metrics to firestore
def converter(state: FeedbackState):
    bsky_metrics_to_firestore(state["post_metrics"])

# compares metrics to current prompt/s
def reviewer(state: FeedbackState):
    dict_video_response, dict_desc_response = review_bsky_metrics(state["post_metrics"])
    return {"dict_video_response": dict_video_response, "dict_desc_response": dict_desc_response}

def stager(state: FeedbackState, config: RunnableConfig):
    thread_id = config["configurable"].get("thread_id")
    stage_prompts_for_review(state["post_metric_summary"], state["dict_video_response"], state["dict_desc_response"], thread_id)


def updater(state: FeedbackState, config: RunnableConfig):
    thread_id = config["configurable"].get("thread_id")
    bsky_prompt_changes_to_firestore(thread_id)


graph = StateGraph(FeedbackState)
client = firestore.Client(project=PROJECT_ID)
memory = FirestoreSaver(project_id=PROJECT_ID)
config = {"configurable": {"thread_id": f"{date.today()}_test_10210"}}

graph.add_node("starter", starter)
graph.add_node("extracter", extracter)
graph.add_node("converter", converter)
graph.add_node("reviewer", reviewer)
graph.add_node("stager", stager)
graph.add_node("updater", updater)

graph.add_edge(START, "starter")
graph.add_edge("starter", "extracter")
graph.add_edge("extracter", "converter")
graph.add_edge("converter", "reviewer")
graph.add_edge("reviewer", "stager")
graph.add_edge("stager", "updater")
graph.add_edge("updater", END)

app = graph.compile(interrupt_before=["updater"], checkpointer=memory)

if __name__ == "__main__":
    snapshot = app.get_state(config)
    if snapshot.next:
        app.invoke({}, config=config)
    else:
        app.invoke({}, config=config)
