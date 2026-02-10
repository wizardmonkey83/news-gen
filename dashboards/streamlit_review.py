import streamlit as st
import pandas as pd
import sys
import os
import ast
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import firestore
from config import PROJECT_ID

st.set_page_config(layout="wide")

client = firestore.Client(project=PROJECT_ID)

# loads streamlit dashboard with both old and new prompts for easy revision ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def get_all_payloads_from_firestore():

    collection_ref = client.collection("news_gen_prompt_reviews")
    documents = collection_ref.stream()
    
    pending_docs = {}
    for document in documents:
        dict_document = document.to_dict()

        if dict_document.get("metadata", {}).get("status", "") == "pending":
            pending_docs[document.id] = dict_document

    return pending_docs

def save_prompt_edits_to_firetore(payload: dict, thread: str):

    document_ref = client.collection("news_gen_prompt_reviews").document(thread)
    document_ref.set(payload)

# streamlit docs: https://docs.streamlit.io/develop/api-reference/
def generate_review_page():
    pending_payloads = get_all_payloads_from_firestore()

    if not pending_payloads:
        st.success("No changes to review, all caught up.")

    # w gemini
    selected_thread_id = st.sidebar.selectbox(
        "Select Review",
        options=list(pending_payloads.keys()),
        format_func=lambda x: f"Task: {x} ({pending_payloads[x]['metadata'].get('generated_at', 'N/A')})"
    )

    thread = selected_thread_id
    payload = pending_payloads[selected_thread_id]

    metrics_summary = payload.get("metrics_summary", {})
    new_video_prompt, new_desc_prompt = payload.get("new_video_prompt", {}), payload.get("new_desc_prompt", {})
    old_video_prompt, old_desc_prompt = payload.get("old_video_prompt", {}), payload.get("old_desc_prompt", {})

    new_video_prompt_df, new_desc_prompt_df = pd.DataFrame([new_video_prompt]), pd.DataFrame([new_desc_prompt])

    summary_tab, video_tab, desc_tab = st.tabs(["Summary", "Video Prompts", "Description Prompts"])

    with summary_tab:
        st.write("Metric Summary")
        col1_summary_container = st.container(border=True)
        with col1_summary_container:
            st.write(f"{metrics_summary}")

    with video_tab:
        old_col, new_col = st.columns(2)
        with old_col:
            col1_video_prompt_expander = st.expander("Current")

            with col1_video_prompt_expander:
                st.json(old_video_prompt)

        with new_col:
            col2_video_prompt_expander = st.expander("New (Editable)")

            editable_data = []
            for k, v in new_video_prompt.items():
                editable_data.append({
                    "Key": k,
                    # json.dumps makes it a string, indent=2 makes it readable
                    "Value": json.dumps(v, indent=2) 
                })
            
            df_video = pd.DataFrame(editable_data)

            # 2. RENDER THE EDITOR
            edited_video_df = st.data_editor(
                df_video,
                use_container_width=True,
                hide_index=True,
                disabled=["Key"], # Lock the keys
                key="video_editor",
                column_config={
                    "Value": st.column_config.TextColumn(
                        "Prompt Content (JSON)",
                        width="large",
                        help="Edit the JSON value. Ensure brackets {} match."
                    )
                }
            )
                
            with col2_video_prompt_expander:
                st.data_editor(new_video_prompt_df, key="video_prompt_df", num_rows="dynamic")

                


    with desc_tab:
        old_col, new_col = st.columns(2)

        with old_col:
            col1_desc_prompt_expander = st.expander("Current")

            with col1_desc_prompt_expander:
                st.json(old_desc_prompt)

        with new_col:
            col2_desc_prompt_expander = st.expander("New (Editable)")

            with col2_desc_prompt_expander:
                    st.data_editor(new_desc_prompt_df, key="desc_prompt_df", num_rows="dynamic")
                
        
    save_btn = st.button("Save")

    if save_btn:
        dict_video_prompt = new_video_prompt_df.to_dict(orient="records")[0]
        dict_desc_prompt = new_desc_prompt_df.to_dict(orient="records")[0]

        payload["new_video_prompt"] = dict_video_prompt
        payload["new_desc_prompt"] = dict_desc_prompt
        payload["metadata"]["status"] = "complete"

        prompt_review_ref = client.collection("news_gen_prompt_reviews").document(thread)
        prompt_review_ref.set(payload)
