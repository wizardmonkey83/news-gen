from config import BUCKET_NAME, PROJECT_ID, SYNC_LABS_API_KEY

import tempfile
from google.cloud import storage
from moviepy.video.io.VideoFileClip import VideoFileClip, AudioFileClip
from sync import Sync
import time
import os
import requests
from sync.common import Audio, GenerationOptions, Video

# splices together the visual and audio files to create a video --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# synclabs POST docs: https://docs.sync.so/api-reference/api/generate-api/create-with-files
# synclabs GET docs: https://docs.sync.so/api-reference/api/generate-api/get
# moviepy docs: https://zulko.github.io/moviepy/index.html
def align_visual_and_audio(gs_link: str, visual_duration: float, audio_duration: float, storage_prefix: str):

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

    # will use later to crop videos if they get too long
    tail_secs = visual_duration - audio_duration
    max_tail_secs = 2.0

    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)

        visual_blob = bucket.blob(f"{storage_prefix}/visual.mp4")
        visual_blob.download_to_filename(local_visual_path)

        audio_blob = bucket.blob(f"{storage_prefix}/audio.mp3")
        audio_blob.download_to_filename(local_audio_path)

        sync_client = Sync(api_key=SYNC_LABS_API_KEY)

        sync_operation = sync_client.generations.create_with_files(
            model="lipsync-2",
            video=local_visual_path,
            audio=local_audio_path
        )

        while sync_operation.status != "COMPLETED":
            time.sleep(10)
            sync_operation = sync_client.generations.get(sync_operation.id)

        if sync_operation.error:
            print(f"Error during sync_operation: {sync_operation.error}")
            return
        
        # get the actual file. didnt know requests did this.
        sync_operation_response = requests.get(sync_operation.output_url)

        # iterates over chunks to avoid overloading ram by loading it all at once
        with open(local_synced_video_path, 'wb') as temp_synced_video:
            for chunk in sync_operation_response.iter_content(chunk_size=1024):
                temp_synced_video.write(chunk)

        load_synced_video = VideoFileClip(local_synced_video_path)

        # in order to avoid too much blank spac at the end of the video
        if tail_secs > max_tail_secs:
            cut_visual = load_synced_video.subclipped(0, (audio_duration + max_tail_secs))
        else:
            cut_visual = load_synced_video
        
        
        load_audio = AudioFileClip(local_audio_path)
        completed_video = cut_visual.set_audio(load_audio)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_complete_video:
            local_complete_video_path = temp_complete_video.name

        completed_video.write_videofile(local_complete_video_path)
        complete_video_blob = bucket.blob(f"{storage_prefix}/video.mp4")
        complete_video_blob.upload_from_filename(local_complete_video_path)

        return True

    except Exception as e:
        print(f"!!REAL!! ERROR SYNCING VIDEO: {e}")

    finally:
        if os.path.exists(local_visual_path):
            os.remove(local_visual_path)

        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)

        if os.path.exists(local_synced_video_path):
            os.remove(local_synced_video_path)
        
        if os.path.exists(local_complete_video_path):
            os.remove(local_complete_video_path)