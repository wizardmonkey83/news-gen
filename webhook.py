import functions_framework
from core.agent import app
from langchain_core.runnables import RunnableConfig
from config import TOPIC

@functions_framework.http
def handle_response(request):
    request_args = request.args
    request_json = request.get_json(silent=True)

    action = request_args.get('action') or (request_json and request_json.get('action'))
    thread_id = request_args.get('thread_id') or (request_json and request_json.get('thread_id'))

    if not thread_id:
        return "Missing 'thread_id'.", 400
    if not action:
        return "Missing 'action' parameter. Use 'approve' or 'reject'.", 400
    
    config = {"configurable": {"thread_id": thread_id}}

    try:
        if action == "approve":
            app.invoke(None, config=config)
            # kinda an odd way of confirming. html loads as a barebones webpage
            return f"""
            <html>
                <body>
                    <h1 style='color:green'>Approved!</h1>
                    <p>Agent has resumed. Video is being published.</p>
                </body>
            </html>
            """, 200
        
        elif action == "reject":
            app.invoke({"topic": TOPIC, "is_complete": False}, config=config)

            return f"""
            <html>
                <body>
                    <h1 style='color:red'>Rejected.</h1>
                    <p>Cycle reset. Agent is generating a new video for topic: {TOPIC}.</p>
                </body>
            </html>
            """, 200

        else:
            return f"Unknown action: {action}", 400
        
    except Exception as e:
        return f"Internal server error: {e}", 500