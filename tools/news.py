from google import genai
from google.genai import types
from collections import defaultdict
from datetime import date
import requests
import feedparser
import json
from config import TEXT_MODEL, MOCK_NEWS, PROJECT_ID, LOCATION, RSS_FEED, RSS_FEED_ANALYSIS_PROMPT

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def collect_news(topic: str):
    if not MOCK_NEWS:
        # using google search grounding
        # search grounding docs: https://ai.google.dev/gemini-api/docs/google-search
        if not RSS_FEED:
            print("!!REAL!! GENERATING NEWS SUMMARY....")
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
                    # consider adding region to the search
                    contents=f"Today is {today}. Search for the latest news about: {topic}",
                    config=config,
                )

                if response.candidates:
                    candidate = response.candidates[0]

                    if candidate.content and candidate.content.parts:
                        summary = candidate.content.parts[0].text
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
                    # this should be exceedingly rare, fingers crossed...
                    contents = {
                        "summary": "No news found.",
                        "sources": {}
                    }
                    print("!!REAL!! NO NEWS FOUND. SUMMARY GENERATED.")
                    return contents
                    
                contents = {
                    "summary": summary,
                    "sources": dict(sources),
                }

                print("!!REAL!! SUCCESSFULLY CREATED SUMMARY")
                return contents
            
            except Exception as e:
                print(f"!!REAL!! ERROR GENERATING SUMMARY. ERROR: {e}")
                
                contents = {
                    "summary": "Error fetching news.",
                    "sources": {}
                }

                return contents
            

        else:
            # feedparser docs: https://feedparser.readthedocs.io/en/latest/introduction/
            try:
                print("!!REAL!! GATHERING NEWS VIA RSS FEED...")
                url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
                formatted_response = feedparser.parse(url)

                sources = defaultdict(list)
                payload = defaultdict(list)
                for item in formatted_response.entries:
                    title = item["title"]
                    rss_link = item["link"]
                    pub_date = item["pubDate"]
                    if item["summary"]:
                        desc = item["summary"]
                    elif item["summary_detail"]:
                        desc = item["summary_detail"]
                    else:
                        # should be cautious with this. likely includes additional html that may impact models ability to revise.
                        desc = item["description"]
                    if item["source"]:
                        # i think source_url is a proxy redirect link
                        source_url, source_title = item["source"]["href"], item["source"]["title"]
                        sources[source_title].append(source_url)
                    
                    payload[title].append(desc)
                print("!!REAL!! SOURCES GATHERED AND PARSED...")
                response = client.models.generate_content(
                    model=TEXT_MODEL,
                    contents=[RSS_FEED_ANALYSIS_PROMPT, json.dumps(payload)]
                )
                    
                contents = {
                    "summary": response.text,
                    "sources": sources,
                }
                print("!!REAL!! GEMINI SUMMARY GENERATED")
                return contents
            
            except Exception as e:
                print(f"!!REAL!! Error during RSS feed operation. Error: {e}")

                contents = {
                    "summary": "Error fetching news.",
                    "sources": {}
                }

                return contents

        

    else:
        print("GENERATING MOCK NEWS SUMMARY....")
        print("SUCCESSFULLY CREATED MOCK NEWS SUMMARY")
        return {"summary": "Test news summary.", "sources": {}}
