import time
import os
import json
import tempfile
from google import genai
from google.genai import types
from google.cloud import storage
from config import VIDEO_MODEL, MOCK_VIDEO, BUCKET_NAME, PROJECT_ID, LOCATION, LOCAL_DEV, MULTIPLE_VIDEO, VISUAL_EXTENSION_PROMPT, SIMPLE_VIDEO, VISUAL_SCRIPT_NEGATIVE_PROMPT
import math
from moviepy.video.io.VideoFileClip import VideoFileClip, AudioFileClip
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
            gcs_uri=f"gs://{BUCKET_NAME}/news-gen-anchor9-reference.png",
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
    


# single visual + audio generation ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
        blob = bucket.blob("news-gen-anchor9-reference.png")
        blob.download_to_filename(local_ref_img_path)

        looped_img = ImageClip(local_ref_img_path, audio_length)
        looped_img.write_videofile(local_visual_path, codec="libx264", audio=False, verbose=False, logger=None)

        blob = bucket.blob(f"{storage_prefix}/video.mp4")
        blob.upload_from_filename(local_visual_path)

        print("!!REAL!! LOOPED CLIP SAVED TO BUCKET")

    except Exception as e:
        raise Exception(f"!!REAL!! Error looping image: {e}")
        

    finally: 
        if local_ref_img_path and os.path.exists(local_ref_img_path):
            os.remove(local_ref_img_path)

        if local_visual_path and os.path.exists(local_visual_path):
            os.remove(local_visual_path)


