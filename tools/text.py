from google import genai
from google.genai import types
from config import MOCK_DESC, MOCK_VIDEO, TEXT_MODEL, PROJECT_ID, LOCATION, TEXT_TO_SPEECH_GUIDELINES_PROMPT, VISUAL_SCRIPT_GUIDELINES_PROMPT

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# creates description to go along with the video -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_description(gs_link: str, prompt: str):
    if not MOCK_DESC and not MOCK_VIDEO:
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
    
# creates script to feed to tts audio generation --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_text_to_speech_script(news_summary: str):

    response = client.models.generate_content(
        model=TEXT_MODEL, 
        contents=[TEXT_TO_SPEECH_GUIDELINES_PROMPT, news_summary]
    )

    audio_script = response.text
    return audio_script

# creates script to feed to visual generation -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def generate_visual_script(audio_script: str):

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=[VISUAL_SCRIPT_GUIDELINES_PROMPT, audio_script]
    )

    visual_script = response.text
    return visual_script