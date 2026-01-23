import time
import os
import tempfile
from google import genai
from google.genai import types
from google.cloud import storage
from config import VIDEO_MODEL, MOCK_VIDEO, BUCKET_NAME, TEXT_MODEL, PROJECT_ID, LOCATION, LOCAL_DEV
import random
from datetime import timedelta

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def generate_signed_url(bucket_name, blob_name):
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        # think 24 is good
        expiration=timedelta(hours=24),
        method="GET",
    )
    return url

def generate_video(prompt: str, storage_prefix: str):
    if not MOCK_VIDEO:
        print("!!REAL!! GENERATING VIDEO....")

        filename = "video.mp4"
        if not LOCAL_DEV:
            local_path = f"/tmp/{filename}"
        else:
            local_path = os.path.join(tempfile.gettempdir(), filename)

        operation = client.models.generate_videos(
            model=VIDEO_MODEL,
            prompt=prompt,
        )

        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)

        if operation.error:
            print(f"!!! VIDEO GENERATION FAILED !!!")
            print(f"Error: {operation.error}")

        generated_video = operation.response.generated_videos[0]
        # vertex requires videos to be saved to a local point on the device meaning a gs url cant be saved. saving a temp file bypasses this restraint.
        generated_video.video.save(local_path)

        storage_client = storage.Client(project=PROJECT_ID)
        storage_path = f"{storage_prefix}/{filename}"
        bucket = storage_client.bucket(BUCKET_NAME)
        # blob is just another name for file
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(local_path)

        # cleanup
        if os.path.exists(local_path):
            os.remove(local_path)

        print("!!REAL!! SUCCESSFULLY CREATED VIDEO")

        signed_url = generate_signed_url(BUCKET_NAME, storage_path)
        return {
            "video_url": signed_url, 
            "gs_link": f"gs://{BUCKET_NAME}/{storage_path}", 
        }
    else:
        print("GENERATING MOCK VIDEO.....")
        print("SUCCESSFULLY CREATED MOCK VIDEO")

        filename = "mock_video.mp4"
        return {
            "video_url": "no/url/for/now",
            "gs_link": f"gs://{BUCKET_NAME}/mock_video.mp4", 
        }
    
def generate_description(gs_link: str, prompt: str):
    if not MOCK_VIDEO:
        print("!!REAL!! GENERATING POST DESCRIPTION....")

        video = types.Part.from_uri(
            file_uri=gs_link,
            mime_type="video/mp4"
        )

        response = client.models.generate_content(
            model=TEXT_MODEL, 
            contents=[video, prompt]
        )

        print("!!REAL!! POST DESCRIPTION SUCCESSFULLY CREATED")
        return response.text
    else:
        print("GENERATING MOCK POST DESCRIPTION....")
        print("SUCCESSFULLY CREATED MOCK POST DESCRIPTION")
        return "Wow, this video is super awesome and you should totally watch it!"