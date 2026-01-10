from decouple import config

PROJECT_ID = config("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = config("GOOGLE_CLOUD_REGION")
BUCKET_NAME = config("BUCKET_NAME")

# for testing purposes its a bit cheaper than 3.0
TEXT_MODEL = "gemini-2.5-pro"
VIDEO_MODEL = "veo-3.1-fast-generate-preview"

# for testing theres no need to generate videos or post to socials
MOCK_VIDEO = True
MOCK_SOCIAL = True

# this should be easy to access in order of changes
# this needs to be overly intricate
SYSTEM_PROMPT = """
    You are an XBOX controller.
"""
VIDEO_PROMPT = """
    You are an angry, frustrated goldfish.
"""

# will change everyday, so not sure how this will work
TOPIC = "Index Cards"

