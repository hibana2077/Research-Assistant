import os
import requests
import streamlit as st

from ..utils.data import get_paper_idea

@st.dialog("View Paper Idea")
def view_paper_dialog(idea_name):
    tab1, tab2 = st.tabs(["Keyword", "TBD"])
    with tab1:
        st.write("Here are the keywords for the paper idea:")