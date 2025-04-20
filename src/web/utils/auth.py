import os
import requests

BACKEND_SERVER = os.getenv("BACKEND_SERVER", "http://localhost:8000")

def login(username: str, password: str) -> bool:
    """
    Login to the system.
    """
    url = f"{BACKEND_SERVER}/login"
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        return False
    
def register(username: str, password: str) -> bool:
    """
    Register a new user.
    """
    url = f"{BACKEND_SERVER}/register"
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        return False
