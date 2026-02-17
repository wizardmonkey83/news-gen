from google import genai
from google.genai import types
import json
from config import MOCK_DESC, MOCK_VIDEO, TEXT_MODEL, PROJECT_ID, LOCATION, TEXT_TO_SPEECH_GUIDELINES_PROMPT, VISUAL_SCRIPT_GUIDELINES_PROMPT, SIMPLE_AUDIO

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# creates description to go along with the video -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_description(prompt: str, news_summary: str):
    if not MOCK_DESC and not MOCK_VIDEO:
        print("!!REAL!! GENERATING POST DESCRIPTION....")

        response = client.models.generate_content(
            model=TEXT_MODEL, 
            contents=[news_summary, str(prompt)]
        )

        print("!!REAL!! POST DESCRIPTION SUCCESSFULLY CREATED")
        return response.text
    else:
        print("GENERATING MOCK POST DESCRIPTION....")
        print("SUCCESSFULLY CREATED MOCK POST DESCRIPTION")
        return "Wow, this video is super awesome and you should totally watch it!"
    
# creates script to feed to tts audio generation --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_text_to_speech_script(news_summary: str, num_extensions: str):
    if not SIMPLE_AUDIO:
        print("!!REAL!! GENERATING TEXT-TO-SPEECH SCRIPT...")

        target_length = (int(num_extensions) * 7) + 8

        TEXT_TO_SPEECH_GUIDELINES_PROMPT["target_duration"] = str(target_length)

        response = client.models.generate_content(
            model=TEXT_MODEL, 
            contents=[json.dumps(TEXT_TO_SPEECH_GUIDELINES_PROMPT), news_summary]
        )

        audio_script = response.text

        print("!!REAL!! TEXT-TO-SPEECH SCRIPT GENERATED")

    else:
        audio_script = "Se preparo, se puso linda, sus amigas llamaban, salio de rumba nada le importo"
    return audio_script

# creates script to feed to visual generation -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_visual_script(audio_script: str):

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=[json.dumps(VISUAL_SCRIPT_GUIDELINES_PROMPT), audio_script]
    )

    visual_script = response.text
    return visual_script