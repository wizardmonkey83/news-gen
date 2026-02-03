import google.auth
from datetime import date
from google.cloud import storage, firestore
import tempfile
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import json
from config import PROJECT_ID, BUCKET_NAME, MOCK_DESC

# in case google drive wants to give me permission
"""
def create_folder(topic: str):
    creds, _ = google.auth.default()

    try:
        service = build("drive", "v3", credentials=creds)

        page_token = None
        # i shouldn't need the while loop since there should only be one response but docs want it...
        while True:
            response = (
                service.files().list(
                    q=f"mimeType='application/vnd.google-apps.folder' and fullText='{topic} -- {date.today()}'",
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                )
                .execute()
            )
            # file found
            if response:
                for file in response.get("files", []):
                    if file.get("name") == f"{topic} -- {date.today()}":
                        return file.get("id")
            else:
                break


        file_metadata = {
            "name": f"{topic} -- {date.today()}",
            "parents": [FOLDER_ID],
            "mimeType": "application/vnd.google-apps.folder",
        }
        file = service.files().create(body=file_metadata, fields="id").execute()
        return file.get("id")
    
    except HttpError as e:
        print(f"An error occurred: {e}")
        return None


def video_to_drive(filename: str, folder_id: str):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        local_video_path = temp_video.name
    
    media = None
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.download_to_filename(local_video_path)

        creds, _ = google.auth.default()
        
        service = build("drive", "v3", credentials=creds)
        file_metadata = {"name": "Video", "parents": [folder_id]}

        media = MediaFileUpload(
            local_video_path, mimetype="video/mp4", resumable=True
        )

        file = (
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        )
        return file.get("id")
    finally:
        # lets the file get deleted if the script crashes during upload
        if media:
            del media

        if os.path.exists(local_video_path):
            os.remove(local_video_path)
"""
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
def bsky_metrics_to_firestore(metrics: list):
    print("!!REAL!! BSKY METRICS UPLOAD STARTING...")
    # this is fine for now. maybe edit it to be a range.
    today = date.today()

    client = firestore.Client(project=PROJECT_ID)
    new_metrics_ref = client.collection("news_gen_post_metrics").document(f"BSKY_week_of_{today}")
    # this should fulfil the dict requirement....
    new_metrics_ref.set({"metrics": metrics})
    print("!!REAL!! BSKY METRICS SAVED TO FIRESTORE")
    return True

# save updated prompts to firestore ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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

    for key in dict_video_response.keys():
        curr_dict_video_prompt[key] = dict_video_response[key]

    for key in dict_desc_response.keys():
        curr_dict_desc_prompt[key] = dict_desc_response[key]

    # remember you cant push to a snapshots
    video_prompt_ref.set(curr_dict_video_prompt)
    desc_prompt_ref.set(curr_dict_desc_prompt)
    
    print("!!REAL!! PROMPT UPDATES SAVED TO FIRESTORE")
    return True






