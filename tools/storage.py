import google.auth
from datetime import date
import tempfile
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import FOLDER_ID

def video_to_drive(topic: str):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        local_video_path = temp_video.name
    
    try:
        creds, _ = google.auth.default()
        
        service = build("drive", "v3", credentials=creds)
        file_metadata = {"name": f"{topic} -- {date.today()}", "parents": [FOLDER_ID]}

        media = MediaFileUpload(
            local_video_path, mimetype="video/mp4", resumable=True
        )

        file = (
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        )
        return file.get("id")
    finally:
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
