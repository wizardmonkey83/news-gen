from google import genai
from google.genai import types
from config import MOCK_DESC, MOCK_VIDEO, TEXT_MODEL, PROJECT_ID, LOCATION

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

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