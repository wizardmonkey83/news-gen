# News-Gen: An AI Agent

This repo contains the code for a news generation agent that creates short form videos with accompanying descriptions that are posted to social media. While the current application is social media posting, the agent is robust and can be altered slightly to serve different purposes.

## Tools Used 

__LangChain:__ for defining the structure of the model. 

__Firestore:__ for keeping track of the agents checkpoints, backing up a record of the agent after the completion of each node in case of interruption. Additionally stores prompts and post engagement metrics.

__Vertex AI (Gemini, VEO):__ for up-to-date news collection, video generation, analysis, and a bunch of other uses.

__Google Sheets API:__ for information ingestion, ease of access.

__AT Protocol:__ for interacting with BlueSky API.

## Repository Structure
```
/news-gen
|---/core
|   |---__init__.py
|   |---agent.py            # Stores the news-gen agent structure (this gets run)
|   |---analyst.py          # Stores the feedback loop agent (this also gets run, but less often)
|   |---state.py            # Stores the class definition for all agents
|
|---/temp
|   |---prompts_to_firebase.py      # Small helper script that uploads prompts to Firestore for the first time
|
|---/tools
|   |---__init__.py
|   |---engagement.py       # Extracts metrics from BlueSky Post URLs
|   |---news.py             # Generates a news summary and list of sources for a given topic
|   |---notification.py     # Sends an approval email to a HITL
|   |---sentiment.py        # Analyzes extracted metrics to determine overall sentiment towards post
|   |---sheets.py           # Reads and writes data to a master sheet containing topic, sources, etc
|   |---social.py           # Publishes posts to social media
|   |---storage.py          # Stores items to buckets and firestore
|   |---video.py            # Generates videos
|
|---config.py           # Stores config variables and other information

```

## Agentic Process

