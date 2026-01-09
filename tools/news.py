from google import genai
from google.genai import types
from collections import defaultdict
from datetime import date
from config import TEXT_MODEL

client = genai.Client()

def collect_news(topic: str):
    today = date.today()

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            # this will have to be dynamic
            # also consider adding region to the search
            contents=f"Today is {today}. Search for the latest news about {topic}",
            config=config,
        )

        if response.candidates:
            candidate = response.candidates[0]

            if candidate.content and candidate.content.parts:
                summary = response.candidates.content.parts[0].text
            else:
                summary = "No summary generated."

            sources = defaultdict(list)
            
            if candidate.grounding_metadata and candidate.grounding_metadata.grounding_chunks:
                for chunk in candidate.grounding_metadata.grounding_chunks:
                    if chunk.web:
                        title = chunk.web.title
                        uri = chunk.web.uri
                        sources[title].append(uri)
            
        else:
            # this should be exceedingly rare fingers crossed
            contents = {
                "summary": "No news found.",
                "sources": {}
            }
            return contents
            
        contents = {
            "summary": summary,
            "sources": dict(sources),
        }

        return contents
    # in case of an API issue
    except Exception as e:
        return {"summary": "Error fetching news.", "sources": {}}
