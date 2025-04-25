import os
import requests
import streamlit as st

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    tab1, tab2 = st.tabs(["Keyword", "TBD"])
    with tab1:
        st.write("Here are the keywords for the paper idea:")