import time
import os
import tempfile
from google import genai
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

def generate_video(prompt: str, topic: str):
    if not MOCK_VIDEO:
        print("!!REAL!! GENERATING VIDEO....")
        # think this is a fine way to create titles in case of re-using topics
        num = random.randint(0, 1000)
        filename = f"{topic}_{num}.mp4"
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

        generated_video = operation.response.generated_videos[0]
        # vertex requires videos to be saved to a local point on the device meaning a gs url cant be saved. saving a temp file bypasses this restraint.
        generated_video.video.save(local_path)

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        # blob is just a name for file
        blob = bucket.blob(filename)
        blob.upload_from_filename(local_path)

        # cleanup
        if os.path.exists(local_path):
            os.remove(local_path)
        print("!!REAL!! SUCCESSFULLY CREATED VIDEO")
        return {"video": f"gs://{BUCKET_NAME}/{filename}", "filename": filename}
    else:
        print("GENERATING MOCK VIDEO.....")
        print("SUCCESSFULLY CREATED MOCK VIDEO")
        filename = "mock_video.mp4"
        return {"gs_link": f"gs://{BUCKET_NAME}/mock_video.mp4", "filename": filename}
    
def generate_description(video_url: str, prompt: str, filename: str):
    if not MOCK_VIDEO:
        print("!!REAL!! GENERATING POST DESCRIPTION....")
        storage_client = storage.Client(project=PROJECT_ID)

        if not LOCAL_DEV:
            local_path = f"/tmp/{filename}"
        else:
            local_path = os.path.join(tempfile.gettempdir(), filename)

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.download_to_filename(local_path)

        file = client.files.upload(file=local_path)
        response = client.models.generate_content(
            model=TEXT_MODEL, 
            contents=[file, prompt]
        )

        client.files.delete(name=file.name)
        if os.path.exists(local_path):
            os.remove(local_path)

        print("!!REAL!! POST DESCRIPTION SUCCESSFULLY CREATED")
        return response.text
    else:
        print("GENERATING MOCK POST DESCRIPTION....")
        print("SUCCESSFULLY CREATED MOCK POST DESCRIPTION")
        return "Wow, this video is super awesome and you should totally watch it!"