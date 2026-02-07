from elevenlabs import ElevenLabs
from tinytag import TinyTag
import tempfile
import os
from google.cloud import storage
from config import ELEVEN_LABS_API_KEY, PROJECT_ID, BUCKET_NAME

client = ElevenLabs(
    base_url="https://api.elevenlabs.io",
    api_key=ELEVEN_LABS_API_KEY
)

# create audio snippet using script for video ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# elevenlabs docs: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
def generate_audio_snippet(audio_script: str, storage_prefix: str):
    print("!!REAL!! GENERATING AUDIO")

    local_audio_path = None

    storage_client = storage.Client(project=PROJECT_ID)
    storage_path = f"{storage_prefix}/audio.mp3"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(storage_path)

    try:
        audio = client.text_to_speech.convert(
            # placeholder voice id
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            output_format="mp3_44100_128",
            text=audio_script,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", mode="wb", delete=False) as temp_audio:
            local_audio_path = temp_audio.name
            for chunk in audio:
                temp_audio.write(chunk)

        blob.upload_from_filename(local_audio_path)

        audio_tag = TinyTag.get(local_audio_path)
        audio_length = float(audio_tag.duration)

        print("!!REAL!! AUDIO GENERATED AND SAVED TO BUCKET")
        return audio_length

    except Exception as e:
        raise Exception(f"!!REAL!! ERROR GENERATING AUDIO FILE: {e}")

    finally:
        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)