import streamlit as st
import os
import requests

def new_idea(data:dict):
    """
    {
        "paper_name": "Knowledge Base Name",
        "desc": "Knowledge Base Description",
        "icon": "Knowledge Base Icon",
        "username": "Owner Username"
    }
    """
    url = os.getenv("BACKEND_SERVER", "http://localhost:8000") + "/papers/create"
    payload = {
        "paper_name": data["name"],
        "desc": data["desc"],
        "icon": data["icon"],
        "username": data["owner"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

@st.dialog("New Paper Idea")
def new_idea_dialog():
    name = st.text_input("New idea Name", max_chars=20)
    desc = st.text_input("Description")
    icon = st.selectbox("Icon",['📚', '🤖', '👾','⌛','🪐','🩻','🧬'])
    if st.button("Create",key="new_idea_btn"):
        if name == "":
            st.error("Please enter a name for the new knowledge base.")
            return
        if desc == "":
            st.error("Please enter a description for the new knowledge base.")
            return
        if icon == "":
            st.error("Please select an icon for the new knowledge base.")
            return
        if len(name) < 3:
            st.error("Name must be at least 3 characters long.")
            return
        data = {
            "name": name,
            "desc": desc,
            "icon": icon,
            "owner": st.session_state.username
        }
        result = new_idea(data)
        if result:
            st.success("Knowledge base created successfully!")
            st.session_state.new_idea = result
            st.session_state.idea = result
            st.rerun()