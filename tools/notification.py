from config import SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL, APPROVAL_URL
from email.message import EmailMessage
from datetime import date
import smtplib
import mimetypes

def send_request(video_url: str, post_description: str, thread_id: str):
    # creating the message
    message = EmailMessage()
    message["Subject"] = f"AGW MEDIA CONTENT APPROVAL - {date.today()}"
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    
    html = f"""
        <html>
            <body>
                <h1>Click the link to approve and publish the video with associated content.</h1>
                <p>Generated Video: {video_url}</p>
                <p>Post Description: {post_description}</p>
                <p>PLEASE DO NOT DOUBLE CLICK THE APPROVAL/REJECTION LINK. PLEASE DO NOT DOUBLE CLICK THE APPROVAL/REJECTION LINK.</p>
                <p>
                    <a href="{APPROVAL_URL}?action=approve&thread_id={thread_id}">[APPROVE & PUBLISH]</a>
                </p>
                <p>
                    <a href="{APPROVAL_URL}?action=reject&thread_id={thread_id}">[REJECT & RESET]</a>
                </p>
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

    return True

    


    
