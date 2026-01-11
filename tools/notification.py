from config import SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL, APPROVAL_URL
from email.message import EmailMessage
from datetime import date
import smtplib
import mimetypes

def send_request(video_url: str, video_description: str, thread_id: str):
    # creating the message
    message = EmailMessage()
    message["Subject"] = f"AGW MEDIA CONTENT APPROVAL - {date.today()}"
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    
    html = f"""
        <html>
            <body>
                <h1>Click the link to approve and publish the video and associated content.</h1>
                <p>Generated Video: {video_url}</p>
                <p>Video Description: {video_description}</p>
                <p>PLEASE DO NOT DOUBLE CLICK THE APPROVAL LINK. PLEASE DO NOT DOUBLE CLICK THE APPROVAL LINK.</p>
                <p>Approval Link: {APPROVAL_URL}?{thread_id}</p>
            </body>
        </html>
    """
    message.add_alternative(html, subtype="html")

    # establish connections
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)

    


    
