from atproto import Client, models
import time
import os
import requests
from config import MOCK_SOCIAL, BSKY_USERNAME, BSKY_PASSWORD

def post_to_bsky(description: str, video_url: str):
    if not MOCK_SOCIAL:
        print("!!REAL!! UPLOADING VIDEO....")

        client = Client()
        client.login(BSKY_USERNAME, BSKY_PASSWORD)

        service_auth = client.com.atproto.server.get_service_auth({
            "aud": f"did:web:{client._service.host}",
            "lxm": "com.atproto.repo.uploadBlob",
            "exp": int(time.time()) + 1800,
        })

        token = service_auth.token

        with open(video_url, "rb") as video:
            video_data = video.read()

        upload_url = "https://video.bsky.app/xrpc/app.bsky.video.uploadVideo"

        params = {
            "did": client.me.did,
            "name": os.path.basename(video_url)
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "video/mp4"
        }

        response = requests.post(upload_url, params, headers, data=video_data)

        if response.status_code != 200:
            raise Exception(f"Upload Failed: {response.text}")
        
        job_status = response.json()
        job_id = job_status["jobId"]
        blob = job_status.get("blob")

        print("!!REAL!! VIDEO SUBMITTED....")

        while not blob:
            status_res = requests.get(
            "https://video.bsky.app/xrpc/app.bsky.video.getJobStatus",
            params={'jobId': job_id},
            headers={'Authorization': f'Bearer {token}'}
            )
        
            status_data = status_res.json()
            job_state = status_data['jobStatus']['state']
            progress = status_data['jobStatus'].get('progress', 0)
            
            print(f"Status: {job_state} ({progress}%)")
            
            if job_state == 'JOB_STATE_COMPLETED':
                blob = status_data['jobStatus']['blob']
                break
            elif job_state == 'JOB_STATE_FAILED':
                raise Exception("Video processing failed on Bluesky server.")
            
            time.sleep(2)

        print("!! VIDEO PROCESSED SUCCESSFULLY...")

        aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(width=1920, height=1080)

        client.send_post(
            text=description,
            embed=models.AppBskyEmbedVideo.Main(
                video=blob,
                aspect_ratio=aspect_ratio
            )
        )

        print("!!REAL!! POST PUBLISHED....")

        
