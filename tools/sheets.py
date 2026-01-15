import google.auth
from googleapiclient.discovery import build
from config import SPREADSHEET_ID


def get_topic():
    creds, _ = google.auth.default()
    service = build("sheets", "v4", credentials=creds)

    read_range = "AGW Studios News Queue!A:B"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=read_range
    ).execute()

    values = result.get("values", [])
    
    if not values:
        # shouldn't happen
        return None

    # add a "In progress" check to tell the agent to sleep
    for i, row in enumerate(values, start=1):
        if len(row) < 2:
            continue
        topic, status = row[0], row[1]
        if status.strip().lower() == "pending":
            update_range = f"AGW Studios News Queue!B{i}"

            body = {
                "values": [["In Progress"]]
            }

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="RAW",
                body=body
            ).execute()

            return topic
    return None
    # assumes there is a topic 
    


    