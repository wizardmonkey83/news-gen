import google.auth
from datetime import date
from google.cloud import storage
import tempfile
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from config import FOLDER_ID, PROJECT_ID, BUCKET_NAME

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

def desc_to_bucket(description: str, storage_prefix: str):
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