from decouple import config

PROJECT_ID = config("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = config("GOOGLE_CLOUD_REGION")
BUCKET_NAME = config("BUCKET_NAME")

SENDER_EMAIL = config("SENDER_EMAIL")
SENDER_PASSWORD = config("SENDER_PASSWORD")
RECIPIENT_EMAIL = config("RECIPIENT_EMAIL")
APPROVAL_URL = config("APPROVAL_URL")

SPREADSHEET_ID = config("SPREADSHEET_ID")


# for testing purposes its a bit cheaper than 3.0
TEXT_MODEL = "gemini-2.5-pro"
VIDEO_MODEL = "veo-3.1-fast-generate-preview"

# for testing theres no need to generate videos or post to socials
MOCK_VIDEO = True
MOCK_NEWS = True
MOCK_SOCIAL = True
LOCAL_DEV = True

# this should be easy to access in order of changes
# this needs to be overly intricate
SYSTEM_PROMPT = """
    You are an XBOX controller.
"""
VIDEO_PROMPT = """
    You are an angry, frustrated goldfish.
"""
DESCRIPTION_PROMPT = """
    Write a nice, detailed description on the events that occur in the video
"""


