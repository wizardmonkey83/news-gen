import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from flask import Flask, render_template, request, jsonify
from google.cloud import storage
import uuid

from config import BUCKET_NAME, PROJECT_ID
from core.agent import app as agent_app

app = Flask(__name__)

def upload_to_gcs(file, destination_blob_name):
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    
    blob.upload_from_file(file, content_type=file.content_type)
    return f"gs://{BUCKET_NAME}/{destination_blob_name}"

@app.route('/')
def index():
    return render_template('start.html')

@app.route('/generate', methods=['POST'])
def generate_video():
    try:

        topic = request.form.get('topic')
        extensions_input = request.form.get('extensions', '0')
        file = request.files.get('file')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        try:
            num_extensions = int(extensions_input)
        except ValueError:
            num_extensions = 0

        reference_image_uri = None
        if file and file.filename != '':
            filename = f"demo_uploads/{uuid.uuid4()}_{file.filename}"
            reference_image_uri = upload_to_gcs(file, filename)
            print(f"File uploaded to: {reference_image_uri}")
        

        thread_id = f"web_demo_{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "topic": topic,
            "num_extensions": num_extensions,
            "reference_image_uri": reference_image_uri,
            "is_complete": False
        }

        final_state = agent_app.invoke(initial_state, config=config)

        video_url = final_state.get("video_url")
        post_description = final_state.get("post_description")
        
        return jsonify({"status": "success", "video_url": video_url, "description": post_description})

    except Exception as e:
        print(f"Error in /generate: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/publish')
def publish():
    video_url = request.args.get('video')
    return render_template('publish.html', video_url=video_url)

if __name__ == '__main__':
    app.run(debug=True, port=8080)