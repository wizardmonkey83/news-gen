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
                    contents=f"Today is {today}. Search for news about: {topic}. Generate as detailed a summary as possible.",
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
                # cant contain control characters
                url = url.replace(" ", "%20")
                formatted_response = feedparser.parse(url)

                sources = defaultdict(list)
                payload = defaultdict(list)
                for item in formatted_response.entries:
                    title = item.get("title")
                    rss_link = item.get("link")
                    if item.get("pubDate"):
                        pub_date = item.get("pubDate", "No publication date for source found")

                    if item.get("summary"):
                        desc = item.get("summary")
                    elif item.get("summary_detail"):
                        desc = item.get("summary_detail")
                    else:
                        # should be cautious with this. likely includes additional html that may impact models ability to revise.
                        desc = item.get("description", "no description/summary for source found")
                    if item.get("source"):
                        # i think source_url is a proxy redirect link
                        source_url, source_title = item["source"]["href"], item["source"]["title"]
                        sources[source_title].append(source_url)
                    
                    payload[title].append(desc)
                print("!!REAL!! SOURCES GATHERED AND PARSED...")
                
                response = client.models.generate_content(
                    model=TEXT_MODEL,
                    contents=[json.dumps(RSS_FEED_ANALYSIS_PROMPT), json.dumps(payload)]
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


def collect_rss_sources_for_review(topic: str):
    try:

        url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
        url = url.replace(" ", "%20")
        formatted_response = feedparser.parse(url)

        sources = defaultdict(list)
        serializable_formatted_response = []

        for item in formatted_response.entries:
            title = item.get("title")
            rss_link = item.get("link")
            if item.get("pubDate"):
                pub_date = item.get("pubDate", "No publication date for source found")

            if item.get("summary"):
                desc = item.get("summary")
            elif item.get("summary_detail"):
                desc = item.get("summary_detail")
            else:
                # should be cautious with this. likely includes additional html that may impact models ability to revise.
                desc = item.get("description", "no description/summary for source found")
            if item.get("source"):
                # i think source_url is a proxy redirect link
                source_url, source_title = item["source"]["href"], item["source"]["title"]
                sources[source_title].append(rss_link)

            serializable_formatted_response.append({"title": title, "link": rss_link, "summary": desc})

        rss_feed_response = {"entries": serializable_formatted_response}

        return sources, rss_feed_response

    except Exception as e:
        return Exception(f"Error collecting RSS sources for review: {e}")
    
def filter_selected_rss_sources(approved_sources: dict, rss_feed_response: dict):
    if not approved_sources:
        return rss_feed_response
    
    try:
        payload = defaultdict(list)
        approved_urls = {url for urls in approved_sources.values() for url in urls}

        for item in rss_feed_response.get("entries", []):
            title = item.get("title")
            
            article_link = item.get("link") 
            if article_link in approved_urls:
                if item.get("summary"):
                    desc = item.get("summary")
                elif item.get("summary_detail"):
                    desc = item.get("summary_detail")
                else:
                    desc = item.get("description", "no description/summary for source found")
                
                payload[title].append(desc)
                
        return dict(payload)
    
    except Exception as e:
        return Exception(f"Error filtering RSS source list: {e}")