import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from flask import Flask, render_template, request, jsonify
from google.cloud import storage, firestore
import uuid

from config import BUCKET_NAME, PROJECT_ID, VISUAL_SCRIPT_GUIDELINES_PROMPT, DESCRIPTION_PROMPT
from tools.storage import bsky_to_firestore_recursive_update, bsky_prompt_changes_to_firestore
from core.agent import app as agent_app
from core.feedback import app as feedback_app

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
            "thread_id": thread_id,
        }

        final_state = agent_app.invoke(initial_state, config=config)

        video_url = final_state.get("video_url")
        post_description = final_state.get("post_description")
        
        return jsonify({"status": "success", "video_url": video_url, "description": post_description, "thread_id": thread_id})

    except Exception as e:
        print(f"Error in /generate: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/publish')
def publish():
    video_url = request.args.get("video")
    post_description = request.args.get("post_description")
    thread_id = request.args.get("thread_id")

    if thread_id == "null" or thread_id is None:
        return "Error: Session ID lost. Please go back and regenerate.", 400

    return render_template("publish.html", video_url=video_url, thread_id=thread_id, post_description=post_description)

@app.route("/publish/content", methods=["POST"])
def publish_content():
    data = request.get_json()
    socials = data.get("socials", [])
    thread_id = data.get("thread_id")

    if not socials:
        return jsonify({"error": "Select at least one platform."}), 400
    
    if not thread_id:
        return jsonify({"error": "Missing session ID."}), 400

    config = {"configurable": {"thread_id": thread_id}}

    agent_app.update_state(config, {"post_platforms": socials})

    try:
        final_state = agent_app.invoke(None, config=config)
        post_urls = final_state.get("post_urls", {})

        return jsonify({"status": "success", "urls": post_urls})
    
    except Exception as e:
        print(f"Publishing error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500
    


@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/feedback/collect", methods=["POST"])
def collect_feedback():
    try:

        urls = request.form.get('urls')

        if isinstance(urls, str):
            url_list = [u.strip() for u in urls.split(",")]
        else:
            url_list = urls
        

        thread_id = f"feedback_demo_{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "bsky_post_urls": url_list
        }

        final_state = feedback_app.invoke(initial_state, config=config)

        post_metric_summary = final_state.get("post_metric_summary")
        new_video_prompt = final_state.get("dict_video_response")
        new_desc_prompt = final_state.get("dict_desc_response")
        
        return jsonify({"status": "success", "post_metric_summary": post_metric_summary, "old_video_prompt": VISUAL_SCRIPT_GUIDELINES_PROMPT, "old_desc_prompt": DESCRIPTION_PROMPT, "new_video_prompt": new_video_prompt, "new_desc_prompt": new_desc_prompt, "thread_id": thread_id})

    except Exception as e:
        print(f"Error in /generate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/feedback/commit", methods=["POST"])
def commit_feedback():
    try:
        data = request.get_json()
        thread_id = data.get("thread_id")
        
        final_video_prompt = data.get("new_video_prompt") 
        final_desc_prompt = data.get("new_desc_prompt")
        
        client = firestore.Client(project=PROJECT_ID)
        staging_ref = client.collection("news_gen_prompt_reviews").document(thread_id)
        
        staging_ref.update({
            "new_video_prompt": final_video_prompt,
            "new_desc_prompt": final_desc_prompt,
            "status": "complete"
        })
        
        bsky_prompt_changes_to_firestore(thread_id)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)