from config import TEXT_MODEL, VIDEO_MODEL, VIDEO_PROMPT, DESCRIPTION_PROMPT, PROJECT_ID
from datetime import datetime
from google.cloud import firestore

def stage_prompts_for_review(metrics_summary: str, dict_video_response: dict, dict_desc_response: dict, thread: str):
    client = firestore.Client(project=PROJECT_ID)

    payload = {
        "metrics_summary": metrics_summary,
        "new_video_prompt": dict_video_response,
        "new_desc_prompt": dict_desc_response,
        "old_video_prompt": VIDEO_PROMPT,
        "old_desc_prompt": DESCRIPTION_PROMPT,
        "metadata": {
            "status": "pending",
            "video_model_version": VIDEO_MODEL,
            "text_model_version": TEXT_MODEL,
            "generated_at": str(datetime.now())
        }
    }

    new_staging_reviews_ref = client.collection("news_gen_prompt_reviews").document(thread)
    new_staging_reviews_ref.set(payload)

    return True