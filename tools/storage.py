from datetime import date
from google.cloud import storage, firestore
import tempfile
import os
import config
from config import PROJECT_ID, BUCKET_NAME, MOCK_DESC

# imports prompts from firestore and loads them into config -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def load_prompts_to_config():
    client = firestore.Client(project=PROJECT_ID)

    video_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_video_prompt")
    desc_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_desc_prompt")
    metric_review_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_metric_review_prompt")
    video_extension_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_video_extension_prompt")
    rss_analysis_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_rss_analysis_prompt")

    video_snap = video_prompt_ref.get()
    desc_snap = desc_prompt_ref.get()
    metric_review_snap = metric_review_prompt_ref.get()
    video_extension_snap = video_extension_prompt_ref.get()
    rss_analysis_snap = rss_analysis_prompt_ref.get()

    dict_video_prompt = video_snap.to_dict()
    dict_desc_prompt = desc_snap.to_dict()
    dict_metric_review_prompt = metric_review_snap.to_dict()
    dict_video_extension_prompt = video_extension_snap.to_dict()
    dict_rss_analysis_prompt = rss_analysis_snap.to_dict()

    config.VIDEO_PROMPT = dict_video_prompt
    config.DESCRIPTION_PROMPT = dict_desc_prompt
    config.METRIC_REVIEW_PROMPT = dict_metric_review_prompt
    config.VIDEO_EXTENSION_PROMPT = dict_video_extension_prompt
    config.RSS_FEED_ANALYSIS_PROMPT = dict_rss_analysis_prompt

    return True

# stores post description to bucket in topic folder --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# bucket docs: https://docs.cloud.google.com/storage/docs/buckets?authuser=1
def desc_to_bucket(description: str, storage_prefix: str):
    if not MOCK_DESC:
        print("!!REAL!! SAVING DESC TO BUCKET...")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_desc:
            local_desc_path = temp_desc.name

        with open(local_desc_path, "w", encoding="utf-8") as file:
            file.write(description)

        filename = "description.txt"

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{storage_prefix}/{filename}")

        blob.upload_from_filename(local_desc_path)

        if os.path.exists(local_desc_path):
            os.remove(local_desc_path)
        print("!!REAL!! DESC SAVED TO BUCKET")
        return True

# saves metrics as json document inside of firestore collection -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# firestore docs: https://firebase.google.com/docs/firestore/manage-data/add-data#python
def bsky_metrics_to_firestore(metrics: dict):
    print("!!REAL!! BSKY METRICS UPLOAD STARTING...")
    # this is fine for now. maybe edit it to be a range.
    today = date.today()

    client = firestore.Client(project=PROJECT_ID)
    new_metrics_ref = client.collection("news_gen_post_metrics").document(f"BSKY_week_of_{today}")

    new_metrics_ref.set({"metrics": metrics})
    print("!!REAL!! BSKY METRICS SAVED TO FIRESTORE")
    return True

def bsky_metrics_summary_to_firestore(metrics_summary: dict):
    today = date.today()
    client = firestore.Client(project=PROJECT_ID)

    new_metrics_summary_ref = client.collection("news_gen_post_metric").document(f"BSKY_week_of_{today}_summary")
    new_metrics_summary_ref.set({"summary": metrics_summary})

    print("!!REAL!! BSKY METRICS SUMMARY SAVED TO FIRESTORE")
    return True

# save updated prompts to firestore ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def bsky_to_firestore_recursive_update(prompt: dict, overrides: dict):
    
    for key, value in overrides.items():
        if isinstance(value, dict) and value:
            returned = bsky_to_firestore_recursive_update(prompt.get(key, {}), value)
            prompt[key] = returned
        else:
            prompt[key] = overrides[key]

        return prompt

# firestore docs: https://firebase.google.com/docs/firestore/manage-data/add-data#python
def bsky_prompt_changes_to_firestore(dict_video_response: dict, dict_desc_response: dict):
    print("!!REAL!! SAVING PROMPT UPDATES TO FIRESTORE....")

    client = firestore.Client(project=PROJECT_ID)
    video_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_video_prompt")
    desc_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_desc_prompt")

    curr_video_snap = video_prompt_ref.get()
    curr_desc_snap = desc_prompt_ref.get()

    curr_dict_video_prompt = curr_video_snap.to_dict()
    curr_dict_desc_prompt = curr_desc_snap.to_dict()

    parsed_dict_video_prompt = bsky_to_firestore_recursive_update(curr_dict_video_prompt, dict_video_response)
    parsed_dict_desc_prompt = bsky_to_firestore_recursive_update(curr_dict_desc_prompt, dict_desc_response)

    # remember you cant push a snapshot
    video_prompt_ref.set(parsed_dict_video_prompt)
    desc_prompt_ref.set(parsed_dict_desc_prompt)
    
    print("!!REAL!! PROMPT UPDATES SAVED TO FIRESTORE")
    return True






