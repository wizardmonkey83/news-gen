import streamlit as st
import pandas as pd
from google.cloud import firestore
from config import PROJECT_ID

client = firestore.Client(project=PROJECT_ID)

def get_payload_from_firestore():

    collection_ref = client.collection("news_gen_prompt_reviews")
    documents = collection_ref.stream()
    
    for document in documents:
        document_snap = document.get()
        dict_document = document_snap.to_dict()

        if dict_document.get("metadata", {}).get("status", "") == "pending":
            thread = document.id
            return dict_document, thread
        
    # cooked
    return None

def save_prompt_edits_to_firetore(payload: dict, thread: str):

    document_ref = client.collection("news_gen_prompt_reviews").document(thread)
    document_ref.set(payload)

# streamlit docs: https://docs.streamlit.io/develop/api-reference/
def generate_review_page():
    payload, thread = get_payload_from_firestore()

    metrics_summary = payload.get("metrics_summary", {})
    new_video_prompt, new_desc_prompt = payload.get("new_video_prompt", {}), payload.get("new_desc_prompt", {})
    old_video_prompt, old_desc_prompt = payload.get("old_video_prompt", {}), payload.get("old_desc_prompt", {})

    new_video_prompt_df, new_desc_prompt_df = pd.DataFrame(new_video_prompt), pd.DataFrame(new_desc_prompt)

    col1_container = st.container()
    col1_summary_container = st.container(border=True)

    col1_video_prompt_expander = st.expander("Old Video Prompt")
    col1_desc_prompt_expander = st.expander("Old Description Prompt")

    with col1_container:
        st.write("Metric Sentiment Summary")

        with col1_summary_container:
            st.write(f"{metrics_summary}")

        with col1_video_prompt_expander:
            st.write(f"{old_video_prompt}")

        with col1_desc_prompt_expander:
            st.write(f"{old_desc_prompt}")


    col2_container = st.container()
    
    col2_video_prompt_expander = st.expander("New Video Prompt")
    col2_desc_prompt_expander = st.expander("New Description Prompt")

    with col2_container:
        
        with col2_video_prompt_expander:
            st.data_editor(new_video_prompt_df, key="video_prompt_df", num_rows="dynamic")

        with col2_desc_prompt_expander:
            st.data_editor(new_desc_prompt_df, key="desc_prompt_df", num_rows="dynamic")
        
    save_btn = st.button("Save")

    if save_btn:
        dict_video_prompt = new_video_prompt_df.to_dict(orient="records")
        dict_desc_prompt = new_desc_prompt_df.to_dict(orient="records")

        payload["new_video_prompt"] = dict_video_prompt
        payload["new_desc_prompt"] = dict_desc_prompt
        payload["metadata"]["status"] = "complete"

        prompt_review_ref = client.collection("news_gen_prompt_reviews").document(thread)
        prompt_review_ref.set(payload)



        


