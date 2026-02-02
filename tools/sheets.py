import google.auth
from googleapiclient.discovery import build
import config
from config import SPREADSHEET_ID, MULTIPLE_VIDEO
from datetime import datetime, timedelta, date

def get_topic():
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)

    read_range = "A:C"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        # shouldn't happen
        return None

    # add a "In progress" check to tell the agent to sleep. 1-indexed
    for i, row in enumerate(values, start=1):
        if len(row) < 3:
            continue
        topic, length_secs, status = row[0], row[1], row[2]
        if status.strip().lower() == "pending":
            update_range = f"C{i}"

            body = {
                "values": [["In Progress"]]
            }

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body
            ).execute()
            print("TOPIC COLLECTED....")

            # even if it becomes 0, it wont matter as its not used outside of MULTIPLE_VIDEOS
            num_extensions = (int(length_secs) - 8) / 7
            if num_extensions > 0:
                config.MULTIPLE_VIDEO = True
            else:
                config.MULTIPLE_VIDEO = False

            print(f"NUM OF VIDEOS --> {num_extensions}")
            return topic, num_extensions
    return None
    # assumes there is a topic 
    
# stores news sources for easy access ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def store_sources(sources: dict):
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)
    # i think this needs to be a-d, maybe not
    read_range = "A:D"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        return None
    
    for i, row in enumerate(values, start=1):
        if len(row) < 3:
            continue
        status = row[2]
        if status.strip().lower() == "in progress":
            sources_cell = f"D{i}"
            formatted_sources = ""
            for title, url in sources.items():
                formatted_sources += f"({title}: {url}), "
            body = {
                "values": [[formatted_sources]]
            }

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=sources_cell,
                valueInputOption="RAW",
                body=body
            ).execute()
            return True 
    return None


# changing "in progress" to "complete" and inserting post urls ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def mark_complete(post_url):
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)

    read_range = "A:C"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        return None
    
    for i, row in enumerate(values, start=1):
        if len(row) < 3:
            continue
        status = row[2]
        if status.strip().lower() == "in progress":
            update_range = f"C{i}"

            body = {
                "values": [["Complete"]]
            }

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body
            ).execute()
            print("!!REAL!! TOPIC MARKED COMPLETE")
            
            # theres gotta be a better way to do this
            update_range = f"E{i}:F{i}"

            body = {
                "values": [[str(date.today()), str(post_url)]]
            }

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body
            ).execute()

            print("!!REAL!! DATE AND POST_URL ADDED TO TOPIC")
            return True
        

    return None


# getting bluesky url -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def get_bsky_url():
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)
    # can this just be "D"?
    read_range = "A:E"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        return None
    
    today = date.today()
    today.split("-")
    curr_year, curr_month, curr_day = today[0], today[1], today[2]

    post_urls = []
    for i, row in enumerate(values, start=1):
        if len(row) < 5:
            continue
        date_added = row[4]
        date_added.split("-")
        row_year, row_month, row_day = date_added[0], date_added[1], date_added[2]

        curr_date = datetime(curr_year, curr_month, curr_day)
        row_date = datetime(row_year, row_month, row_day)
        week_ago = curr_date - timedelta(weeks=1)
        # then its in a valid range. one week for now. 
        if week_ago <= row_date and row_date <= curr_date:
            post_url = row[5]
            post_urls.append(post_url)
            
    return post_urls