import json
import datetime
import time

def make_sse_message(status:str):
    """
    Create a Server-Sent Event message.
    

    - status: The status message to send.
    

    - A formatted SSE message.
    """
    payload = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status
    }
    message = f"data: {json.dumps(payload)}\n\n"
    return message