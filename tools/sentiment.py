from google import genai
from config import PROJECT_ID, LOCATION, TEXT_MODEL, METRIC_REVIEW_PROMPT, LOCAL_FIRESTORE_METRICS, VIDEO_PROMPT, DESCRIPTION_PROMPT
from config import VideoPromptModel, DescriptionPromptModel
import json

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# structured output docs: https://ai.google.dev/gemini-api/docs/structured-output?example=recipe
def review_bsky_metrics(metrics: dict):
    if LOCAL_FIRESTORE_METRICS:
        json_metrics = json.dumps(metrics)

        video_response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=[
                json.dumps(METRIC_REVIEW_PROMPT),
                json_metrics,
            ],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": VideoPromptModel.model_json_schema(),
            },
        )

        json_video_response = VideoPromptModel.model_validate_json(video_response.text)

        desc_response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=[
                json.dumps(METRIC_REVIEW_PROMPT),
                json_metrics
            ],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": DescriptionPromptModel.model_json_schema(),
            },
        )

        json_desc_response = DescriptionPromptModel.model_validate_json(desc_response.text)

        # using .model_dump() since "json_video_response" is an object, not a string 
        dict_video_response = json_video_response.model_dump()
        dict_desc_response = json_desc_response.model_dump()

        return dict_video_response, dict_desc_response
    
        

        

