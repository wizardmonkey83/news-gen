import google.auth
from googleapiclient.discovery import build
from config import SPREADSHEET_ID


def get_topic():
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)

    read_range = "A:B"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        # shouldn't happen
        return None

    # add a "In progress" check to tell the agent to sleep. 1-indexed
    for i, row in enumerate(values, start=1):
        if len(row) < 2:
            continue
        topic, status = row[0], row[1]
        if status.strip().lower() == "pending":
            update_range = f"B{i}"

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
            return topic
    return None
    # assumes there is a topic 
    

def mark_complete():
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)

    read_range = "A:B"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        return None
    
    for i, row in enumerate(values, start=1):
        if len(row) < 2:
            continue
        topic, status = row[0], row[1]
        if status.strip().lower() == "in progress":
            update_range = f"B{i}"

            body = {
                "values": [["Complete"]]
            }

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body
            ).execute()
            print("TOPIC MARKED COMPLETE")
            return True
    return None