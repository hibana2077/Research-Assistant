import requests
import os

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
    
def get_vector_search(paper_name:str, username:str): # TODO
    """
    Get vector search for a paper.
    """
    url = f"{BACKEND_SERVER}/papers/get_vector_search"
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
        return {"status": "fail", "vector_search": []}