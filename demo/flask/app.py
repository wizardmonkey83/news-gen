import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from flask import Flask, render_template, request, jsonify
from google.cloud import firestore
import uuid

from config import BUCKET_NAME, PROJECT_ID, VISUAL_SCRIPT_GUIDELINES_PROMPT, DESCRIPTION_PROMPT
from tools.storage import bsky_to_firestore_recursive_update, bsky_prompt_changes_to_firestore
from tools.news import collect_rss_sources_for_review, filter_selected_rss_sources
from core.agent import app as agent_app
from core.feedback import app as feedback_app

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('start.html')

@app.route("/prepare/sources", methods=["POST"])
def prepare_sources():

    try:
        topic = request.form.get("topic")
        video_length = request.form.get("video_length", 8)

        if not topic:
            return jsonify({"error": "Topic is required."}), 400
        
        thread_id = f"web_demo_{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "topic": topic,
            "video_length": video_length
        }

        agent_app.invoke(initial_state, config=config)
        current_state = agent_app.get_state(config).values
        
        return jsonify({"status": "success", "thread_id": thread_id, "sources": current_state.get("neat_rss_sources", {})})
    
    except Exception as e:
        print(f"Error occurred in /prepare/sources/: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/prepare/script", methods=["POST"])
def prepare_script():
    try:
        data = request.get_json()
        thread_id = data.get("thread_id")
        selected_sources = data.get("selected_sources")

        if not thread_id:
            return jsonify({"error": "Thread ID is required"}), 400

        config = {"configurable": {"thread_id": thread_id}}

        agent_app.update_state(config, {"selected_sources": selected_sources})
        agent_app.invoke(None, config=config)

        current_state = agent_app.get_state(config).values

        return jsonify({"status": "success", "audio_script": current_state.get("audio_script", "")})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate_video():
    try:
        data = request.get_json()
        thread_id = data.get("thread_id")
        final_script = data.get("audio_script")
        selected_anchor = data.get("selected_anchor", "anchor_1.png") 

        if not thread_id:
            return jsonify({"error": "Thread ID is required"}), 400

        config = {"configurable": {"thread_id": thread_id}}

        agent_app.update_state(config, {
            "audio_script": final_script,
            "selected_anchor": selected_anchor
        })

        agent_app.invoke(None, config=config)

        current_state = agent_app.get_state(config).values

        return jsonify({"status": "success", "video_url": current_state.get("video_url"), "description": current_state.get("post_description")})

    except Exception as e:
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