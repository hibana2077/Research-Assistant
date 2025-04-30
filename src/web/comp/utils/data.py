import sseclient
import requests
import os
import streamlit as st

BACKEND_SERVER = os.getenv("BACKEND_SERVER", "http://localhost:8000")

def list_all_paper_idea(username):
    """
    List all paper ideas for a given username.
    """
    url = f"{BACKEND_SERVER}/papers/list"
    payload = {
        "username": username
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail", "papers": []}

def get_paper_idea(paper_name, username):
    """
    Get a paper idea by its name.
    """
    url = f"{BACKEND_SERVER}/papers/get_one"
    payload = {
        "paper_name": paper_name,
        "username": username
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail", "paper": {}}
    
def update_paper_idea(paper_name, username, new_data):
    """
    Update a paper idea by its name.
    """
    url = f"{BACKEND_SERVER}/papers/update"
    payload = {
        "paper_name": paper_name,
        "username": username,
        "new_data": new_data
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail"}
    
def get_related_papers(keywords):
    """
    Get related papers based on keywords.
    """
    url = f"{BACKEND_SERVER}/arxiv/search"
    payload = {
        "query": keywords
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail", "papers": []}

def get_emb_index(paper_name: str, username: str):
    """
    Get embedding index for a paper using SSE.
    """
    url = f"{BACKEND_SERVER}/papers/get_emb_index"
    payload = {
        "paper_name": paper_name,
        "username": username
    }
    # SSE 通常用 GET，但 FastAPI 這裡是 POST，所以用 stream=True
    response = requests.post(url, json=payload, stream=True)
    if response.status_code != 200:
        return {"status": "fail", "vector_search": []}

    client = sseclient.SSEClient(response)
    results = []
    for event in client.events():
        # event.data 會是每次 yield 的訊息
        if event.data == "[DONE]":
            break
        results.append(event.data)
        status = event.data.get("status")
        st.toast(status)
    return {"status": "success", "events": results}