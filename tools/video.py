import time
import os
from google import genai
from google.cloud import storage
from config import VIDEO_MODEL, MOCK_VIDEO, BUCKET_NAME, TEXT_MODEL
import random

client = genai.Client()

def generate_video(prompt: str, topic: str):
    # think this is a fine way to create titles in case of re-using topics
    num = random.randint(0, 1000)
    filename = f"{topic}_{num}.mp4"
    # only allowed to write files to the /tmp directory
    local_path = f"/tmp/{filename}"

    if not MOCK_VIDEO:
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

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        # blob is just a name for file
        blob = bucket.blob(filename)
        blob.upload_from_filename(local_path)

        # cleanup
        if os.path.exists(local_path):
            os.remove(local_path)

        return {"gs_link": f"gs://{BUCKET_NAME}/{filename}", "filename": filename}
    else:
        # to avoid creating test videos
        return {"gs_link": f"gs://{BUCKET_NAME}/mock_video.mp4", "filename": filename}
    
def generate_description(video_url: str, prompt: str, filename: str):
    storage_client = storage.Client()

    local_path = f"/tmp/{filename}"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.download_to_filename(local_path)
    
    gemini_client = genai.Client()

    file = client.files.upload(file=local_path)
    response = client.models.generate_content(
        model=TEXT_MODEL, 
        contents=[file, prompt]
    )
    return response.text