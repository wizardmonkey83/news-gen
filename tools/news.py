from google import genai
from google.genai import types
from collections import defaultdict
import datetime
from config import TEXT_MODEL

def collect_news(topic: str):
    now = datetime.now()
    client = genai.Client()

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    response = client.models.generate_content(
        model=TEXT_MODEL,
        # this will have to be dynamic
        contents=f"Today is {now}. Search for the latest news about {topic}",
        config=config,
    )

    summary = response["candidates"]["content"]["parts"]["text"]
    sources = defaultdict(list)
    
    # time complexity might be an issue
    for url in response["candidates"]["groundingMetadata"]["groundingChunks"]:
        for web in url:
            title = web["title"]
            uri = web["uri"]
            sources[title].append(uri)
            
    contents = {
        "summary": summary,
        "sources": sources,
    }

    return contents

