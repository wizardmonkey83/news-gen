import time
import os
import tempfile
from google import genai
from google.genai import types
from google.cloud import storage
from config import VIDEO_MODEL, MOCK_VIDEO, BUCKET_NAME, TEXT_MODEL, PROJECT_ID, LOCATION, LOCAL_DEV, MULTIPLE_VIDEO, VIDEO_EXTENSION_PROMPT
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

def generate_video(prompt: str, storage_prefix: str, num_extensions="1"):
    # video gen docs: https://ai.google.dev/gemini-api/docs/video?example=dialogue
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

        storage_client = storage.Client(project=PROJECT_ID)
        storage_path = f"{storage_prefix}/{filename}"
        bucket = storage_client.bucket(BUCKET_NAME)
        # blob is just another name for file
        blob = bucket.blob(storage_path)

        if MULTIPLE_VIDEO:
            print(f"!!REAL!! EXTENDING VIDEO {num_extensions}")
            # need to directly upload to bucket due to video length
            bucket_uri = f"gs://{BUCKET_NAME}/{storage_prefix}"

            current_video = generated_video.video
            for i in range(int(num_extensions)):
                print(f"EXTENSION NUMBER --> {i+1}")
                operation = client.models.generate_videos(
                    model=VIDEO_MODEL,
                    video=current_video,
                    prompt=str(VIDEO_EXTENSION_PROMPT),
                    config=types.GenerateVideosConfig(
                        number_of_videos=1,
                        resolution="720p",
                        output_gcs_uri=bucket_uri
                    ),
                )

                while not operation.done:
                    time.sleep(10)
                    operation = client.operations.get(operation)

                if operation.error:
                    print(f"EXTENSION {i+1} FAILED: {operation.error}")

                current_video = operation.response.generated_videos[0].video
                
            # renames video
            final_uri = current_video.uri
            source_blob_name = final_uri.replace(f"gs://{BUCKET_NAME}/", "")
            
            source_blob = bucket.blob(source_blob_name)
            bucket.rename_blob(source_blob, storage_path)

        else:
            generated_video.video.save(local_path)

            # finally save
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
            contents=[video, str(prompt)]
        )

        print("!!REAL!! POST DESCRIPTION SUCCESSFULLY CREATED")
        return response.text
    else:
        print("GENERATING MOCK POST DESCRIPTION....")
        print("SUCCESSFULLY CREATED MOCK POST DESCRIPTION")
        return "Wow, this video is super awesome and you should totally watch it!"