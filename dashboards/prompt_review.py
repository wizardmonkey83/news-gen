from nicegui import ui
from google.cloud import firestore
import sys, os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import PROJECT_ID


client = firestore.Client(project=PROJECT_ID)

def get_pending_prompts():
    
    collection_ref = client.collection("news_gen_prompt_reviews")
    documents = collection_ref.stream()

    for doc in documents:
        dict_doc = doc.to_dict()

        if dict_doc["metadata"]["status"] == "pending":
            return dict_doc, doc.id
        
    return None


# nicegui docs: https://nicegui.io/documentation
def generate_review_dashboard():

    document, thread_id = get_pending_prompts()

    if not document:
        ui.label("No prompts pending review, everything up to date.")

    summary = document.get("metrics_summary", "")
    old_video_prompt, old_desc_prompt = document.get("old_video_prompt", {}), document.get("old_desc_prompt", {})
    new_video_prompt, new_desc_prompt = document.get("new_video_prompt", {}), document.get("new_desc_prompt", {})

    with ui.tabs() as tabs:
        summary_tab = ui.tab("Summary")
        video_tab = ui.tab("Video Prompts")
        desc_tab = ui.tab("Description Prompts")
    
    with ui.tab_panels(tabs, value=desc_tab).classes("w-full"):
        with ui.tab_panel(summary_tab):
            with ui.card():
                ui.label(summary)
        
        with ui.tab_panel(video_tab):
            with ui.column():
                ui.json_editor({"content": {"json": old_video_prompt}, "readOnly": True})
            with ui.column():
                video_editor = ui.json_editor({"content": {"json": new_video_prompt}})

        with ui.tab_panel(desc_tab):
            ui.json_editor({"content": {"json": old_desc_prompt}, "readOnly": True})
            desc_editor = ui.json_editor({"content": {"json": new_desc_prompt}})

    
    def save_prompt_edits():

        dict_video_edits = video_editor.properties["content"]["json"]
        dict_desc_edits = desc_editor.properties["content"]["json"]

        document["new_video_prompt"] = dict_video_edits
        document["new_desc_prompt"] = dict_desc_edits
        document["metadata"]["status"] = "complete"

        prompt_review_ref = client.collection("news_gen_prompt_reviews").document(thread_id)
        prompt_review_ref.set(document) 

        print("Prompt changes set")

    ui.button("Save Changes", on_click=save_prompt_edits)

if __name__ in {"__main__", "__mp_main__"}:
    generate_review_dashboard()

    ui.run(title='Prompt Review Agent', port=8080)