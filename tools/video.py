import time
import os
import json
import tempfile
from google import genai
from google.genai import types
from google.cloud import storage
from config import VIDEO_MODEL, MOCK_VIDEO, BUCKET_NAME, PROJECT_ID, LOCATION, LOCAL_DEV, MULTIPLE_VIDEO, VISUAL_EXTENSION_PROMPT, SIMPLE_VIDEO, VISUAL_SCRIPT_NEGATIVE_PROMPT, DID_API_KEY
import math
import requests
from .sync import generate_signed_url
from moviepy import VideoFileClip, AudioFileClip
from moviepy.video.VideoClip import ImageClip

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# generates only the visuals for the video -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# veo docs: https://ai.google.dev/gemini-api/docs/video?example=dialogue
def generate_visuals(visual_prompt: str, storage_prefix: str, audio_length: float):
    if not MOCK_VIDEO and not SIMPLE_VIDEO:
        filename = "visual.mp4"
        if not LOCAL_DEV:
            local_path = f"/tmp/{filename}"
        else:
            local_path = os.path.join(tempfile.gettempdir(), filename)

        if audio_length <= 8:
            num_extensions = 0
        else:
            num_extensions = math.ceil((audio_length - 8)/7)

        # reference image docs: https://ai.google.dev/gemini-api/docs/video?example=dialogue#reference-images
        visual_reference_image = types.Image(
            gcs_uri=f"gs://{BUCKET_NAME}/anchor9-reference.png",
            mime_type="image/png"
        )

        reference_image_wrapper = types.VideoGenerationReferenceImage(
            image=visual_reference_image,
            reference_type="asset"
        )

        operation = client.models.generate_videos(
            model=VIDEO_MODEL,
            prompt=visual_prompt,
            config=types.GenerateVideosConfig(
                reference_images=[reference_image_wrapper],
                negative_prompt=VISUAL_SCRIPT_NEGATIVE_PROMPT,
                generate_audio=False,
            ),
        )

        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)

        if operation.error:
            print(f"Error generating first video: {operation.error}")

        generated_video = operation.response.generated_videos[0]

        storage_client = storage.Client(project=PROJECT_ID)
        storage_path = f"{storage_prefix}/{filename}"
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(storage_path)

        if num_extensions and num_extensions > 0:
            print(f"!!REAL!! EXTENDING VIDEO {num_extensions}")
            # need to directly upload to bucket due to video length
            bucket_uri = f"gs://{BUCKET_NAME}/{storage_prefix}"

            current_video = generated_video.video
            for i in range(int(num_extensions)):
                print(f"EXTENSION NUMBER --> {i+1}")
                operation = client.models.generate_videos(
                    model=VIDEO_MODEL,
                    video=current_video,
                    prompt=json.dumps(VISUAL_EXTENSION_PROMPT),
                    config=types.GenerateVideosConfig(
                        number_of_videos=1,
                        resolution="720p",
                        output_gcs_uri=bucket_uri,
                        negative_prompt=VISUAL_SCRIPT_NEGATIVE_PROMPT,
                        generate_audio=False
                    ),
                )

                while not operation.done:
                    time.sleep(10)
                    operation = client.operations.get(operation)

                if operation.error:
                    print(f"EXTENSION {i+1} FAILED: {operation.error}")

                current_video = operation.response.generated_videos[0].video
                
            final_video_duration = 8 + (num_extensions * 7)
            # renames video
            final_uri = current_video.uri
            source_blob_name = final_uri.replace(f"gs://{BUCKET_NAME}/", "")
            
            source_blob = bucket.blob(source_blob_name)
            bucket.rename_blob(source_blob, storage_path)
        
        else:
            final_video_duration = 8.0

            generated_video.video.save(local_path)

            # finally save
            blob.upload_from_filename(local_path)

            # cleanup
            if os.path.exists(local_path):
                os.remove(local_path)

        print("!!REAL!! SUCCESSFULLY CREATED VIDEO")

        return {
            "gs_link": f"gs://{BUCKET_NAME}/{storage_path}", 
            "visuals_length": final_video_duration
        }
    

# uses D-ID API to create video from the still image -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_did_video(audio_length: float, storage_prefix: str):
    
    print("!!REAL!! GENERATING D-ID VIDEO...")

    audio_signed_url = generate_signed_url(BUCKET_NAME, f"{storage_prefix}/audio.mp3")
    image_signed_url = generate_signed_url(BUCKET_NAME, "anchor9-reference.png")

    did_url = "https://api.d-id.com/talks"

    payload = {
        "script": {
            "type": "audio",
            "audio_url": audio_signed_url
        },
        "source_url": image_signed_url,
        "config": {
            "fluent": "false",
            "pad_audio": "0.0",
            "stitch": True
        }
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {DID_API_KEY}" 
    }

    response = requests.post(did_url, json=payload, headers=headers)

    if response.status_code != 201:
        raise Exception(f"!!REAL!! D-ID creation failed: {response.text}")
    
    talk_id = response.json().get("id")

    result_url = None
    status = "created"
    while status not in ["done", "error"]:
        time.sleep(5)

        status_url = f"https://api.d-id.com/talks/{talk_id}"
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        status = status_data.get("status")

        if status == "done":
            result_url = status_data.get("result_url")
        elif status == "error":
            raise Exception(f"!!REAL!! D-ID JOB FAILED: {status_data}")

    print("!!REAL!! DOWNLOADING RESULT...")
    
    video_response = requests.get(result_url)

    local_temp_path = None
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        local_temp_path = temp_video.name
        temp_video.write(video_response.content)

    # Upload to GCS
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"{storage_prefix}/video.mp4")
    blob.upload_from_filename(local_temp_path)
    
    # Clean up local file
    if os.path.exists(local_temp_path):
        os.remove(local_temp_path)

    print("!!REAL!! COMPLETE VIDEO SAVED TO BUCKET")

    # Return signed URL for the frontend/agent
    return generate_signed_url(BUCKET_NAME, f"{storage_prefix}/video.mp4")

# single visual + audio generation -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# helper function that slowly zooms in, trying to trigger lipsync
def add_micro_motion(local_visual_path):
    output_path = local_visual_path.replace(".mp4", "_motion.mp4")

    try:
        print("!!REAL!! ADDING MICRO-MOTION TO STATIC CLIP...")
        looped_img = VideoFileClip(local_visual_path)
        w, h = looped_img.size

        def zoom_effect(t):
            return 1 + 0.02 * (t / looped_img.duration)

        moving_clip = (looped_img.resized(zoom_effect).with_position(("center", "center")).with_duration(looped_img.duration))
        
        final_clip = moving_clip.cropped(x1=0, y1=0, width=w, height=h)

        final_clip.write_videofile(output_path, codec="libx264", audio=False, logger=None, fps=24)

        final_clip.close()
        moving_clip.close()
        looped_img.close()

        # Overwrite original
        if os.path.exists(local_visual_path):
            os.remove(local_visual_path)
        os.rename(output_path, local_visual_path)
        
        print("!!REAL!! MICRO-MOTION APPLIED")

    except Exception as e:
        print(f"!!REAL!! Failed to add micro-motion: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)


# moviepy imageclip docs: https://zulko.github.io/moviepy/reference/reference/moviepy.video.VideoClip.ImageClip.html
def loop_image_to_video(audio_length: float, storage_prefix: float):

    local_ref_img_path = None
    local_visual_path = None

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_ref_img:
        local_ref_img_path = temp_ref_img.name

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_visual:
        local_visual_path = temp_visual.name

    try:
        print("!!REAL!! SAVING LOOPED CLIP TO BUCKET...")

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob("anchor9-reference.png")
        blob.download_to_filename(local_ref_img_path)

        looped_img = ImageClip(img=local_ref_img_path, duration=audio_length)
        looped_img.write_videofile(local_visual_path, codec="libx264", audio=False, logger=None, fps=24)

        add_micro_motion(local_visual_path)

        storage_path = f"{storage_prefix}/visual.mp4"
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(local_visual_path)

        print("!!REAL!! LOOPED CLIP SAVED TO BUCKET")

        return {
            "gs_link": f"gs://{BUCKET_NAME}/{storage_path}",
            "visuals_length": audio_length
        }

    except Exception as e:
        raise Exception(f"!!REAL!! Error looping image: {e}")
        

    finally: 
        if local_ref_img_path and os.path.exists(local_ref_img_path):
            os.remove(local_ref_img_path)

        if local_visual_path and os.path.exists(local_visual_path):
            os.remove(local_visual_path)