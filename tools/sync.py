from config import BUCKET_NAME, PROJECT_ID, MOCK_SYNC, REUSE_VIDEO

import tempfile
import time
import json
import os
import requests
from sync import Sync
from datetime import timedelta
from google.cloud import storage
import google.auth 
import google.auth.transport.requests
from moviepy.video.io.VideoFileClip import VideoFileClip, AudioFileClip
from sync.common import GenerationOptions, ActiveSpeaker
from config import SERVICE_ACCOUNT_EMAIL


# splices together the visual and audio files to create a video --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# helper function to generate urls for completed videos
def generate_signed_url(bucket_name, blob_name):
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    credentials, _ = google.auth.default()
    if not credentials.valid:
        credentials.refresh(google.auth.transport.requests.Request())

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=24),
        method="GET",
        service_account_email=SERVICE_ACCOUNT_EMAIL,
        access_token=credentials.token,
    )
    return url

# synclabs POST docs: https://docs.sync.so/api-reference/api/generate-api/create-with-files
# synclabs GET docs: https://docs.sync.so/api-reference/api/generate-api/get
# moviepy docs: https://zulko.github.io/moviepy/index.html
def sync_visual_and_audio(visual_length: float, audio_length: float, storage_prefix: str):

    # to avoid UnboundLocalErrors in the finally block
    local_visual_path = None
    local_audio_path = None
    local_synced_video_path = None
    local_complete_video_path = None

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_visual:
        local_visual_path = temp_visual.name

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        local_audio_path = temp_audio.name

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_synced_video:
        local_synced_video_path = temp_synced_video.name

    try:
        print("!!REAL!! SYNCING VIDEO AND AUDIO...")

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)

        if not REUSE_VIDEO:
            visual_blob = bucket.blob(f"{storage_prefix}/visual.mp4")
            visual_blob.download_to_filename(local_visual_path)
        else:
            visual_blob = bucket.blob(f"reuse_visual.mp4")
            visual_blob.download_to_filename(local_visual_path)

        audio_blob = bucket.blob(f"{storage_prefix}/audio.mp3")
        audio_blob.download_to_filename(local_audio_path)

        if not MOCK_SYNC:
            sync_client = Sync(api_key=None)

            sync_operation = sync_client.generations.create_with_files(
                model="lipsync-2",
                video=local_visual_path,
                audio=local_audio_path
            )

            while sync_operation.status not in ["COMPLETED", "FAILED"]:
                print(f"!!REAL!! SYNC_OPERATION STATUS: {sync_operation.status}")
                time.sleep(10)
                sync_operation = sync_client.generations.get(sync_operation.id)

            if sync_operation.error:
                raise Exception(f"Error during sync_operation: {sync_operation.error}. Status code: {sync_operation.error_code}.")
            
            # get the actual file. didnt know requests did this.
            sync_operation_response = requests.get(sync_operation.output_url)

            print("!!REAL!! VISUAL AND AUDIO SYNCED")

            # iterates over chunks to avoid overloading ram by loading it all at once
            with open(local_synced_video_path, 'wb') as temp_synced_video:
                for chunk in sync_operation_response.iter_content(chunk_size=1024):
                    temp_synced_video.write(chunk)

            load_synced_video = VideoFileClip(local_synced_video_path)
        else:
            load_synced_video = VideoFileClip(local_visual_path)
            visual_length = load_synced_video.duration

        tail_secs = visual_length - audio_length
        max_tail_secs = 1.0

        if tail_secs > max_tail_secs:
            cut_visual = load_synced_video.subclipped(0, (audio_length + max_tail_secs))
        else:
            cut_visual = load_synced_video
        
        print("!!REAL!! CUT VISUAL CREATED...")
        
        load_audio = AudioFileClip(local_audio_path)
        completed_video = cut_visual.with_audio(load_audio)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_complete_video:
            local_complete_video_path = temp_complete_video.name

        print("!!REAL!! WRITING COMPLETED VIDEO FILE...")
        completed_video.write_videofile(local_complete_video_path)

        load_audio.close()
        load_synced_video.close() 
        completed_video.close()

        if cut_visual != load_synced_video:
            cut_visual.close()

        complete_video_blob = bucket.blob(f"{storage_prefix}/video.mp4")
        complete_video_blob.upload_from_filename(local_complete_video_path)

        print("!!REAL!! UPLOADED COMPELTED VIDEO TO BUCKET...")

        signed_url = generate_signed_url(BUCKET_NAME, f"{storage_prefix}/video.mp4")

        print("!!REAL!! COMPLETE VIDEO SAVED TO BUCKET")

        return signed_url

    except Exception as e:
        print(f"!!REAL!! ERROR SYNCING VIDEO: {e}")
        raise Exception

    finally:
        if local_visual_path and os.path.exists(local_visual_path):
            os.remove(local_visual_path)

        if local_audio_path and os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        if local_synced_video_path and os.path.exists(local_synced_video_path):
            os.remove(local_synced_video_path)
        
        if local_complete_video_path and os.path.exists(local_complete_video_path):
            os.remove(local_complete_video_path)