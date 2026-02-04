from google.cloud import firestore
from config import VIDEO_PROMPT, DESCRIPTION_PROMPT, PROJECT_ID

client = firestore.Client(project=PROJECT_ID)

try:
    video_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_video_prompt")
    desc_prompt_ref = client.collection("news_gen_prompts").document("robo_anchor_desc_prompt")

    video_prompt_ref.set(VIDEO_PROMPT)
    desc_prompt_ref.set(DESCRIPTION_PROMPT)

    print("VIDEO AND DESCRIPTION PROMPT UPLOADED TO FIRESTORE")

except Exception as e:

    print(f"UPLOAD FAILED. ERROR: {e}")