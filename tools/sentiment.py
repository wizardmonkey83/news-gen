from google import genai
from config import PROJECT_ID, LOCATION, TEXT_MODEL, METRIC_REVIEW_PROMPT, LOCAL_FIRESTORE_METRICS, VIDEO_PROMPT, DESCRIPTION_PROMPT
from config import VideoPromptModel, DescriptionPromptModel
import json

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def review_bsky_metrics(metrics: list):
    if LOCAL_FIRESTORE_METRICS:
        json_metrics = json.dumps(metrics)

        video_response = client.models.generate_content(
            model=TEXT_MODEL,
            contents={
                "metric_review_prompt": str(METRIC_REVIEW_PROMPT),
                "metrics": json_metrics,
            },
            config={
                "response_mime_type": "application/json",
                "response_json_schema": VideoPromptModel.model_json_schema(),
            },
        )

        json_video_response = VideoPromptModel.model_validate_json(video_response.text)

        desc_response = client.models.generate_content(
            model=TEXT_MODEL,
            contents={
                "metric_review_prompt": str(METRIC_REVIEW_PROMPT),
                "metrics": json_metrics,
            },
            config={
                "response_mime_type": "application/json",
                "response_json_schema": DescriptionPromptModel.model_json_schema(),
            },
        )

        json_desc_response = DescriptionPromptModel.model_validate_json(desc_response.text)

        dict_video_response = json.loads(json_video_response)
        dict_desc_response = json.loads(json_desc_response)

        return dict_video_response, dict_desc_response
    
        

        

