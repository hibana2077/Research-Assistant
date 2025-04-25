import os
import requests
import streamlit as st
import streamlit_tags

from .utils.data import get_paper_idea, update_paper_idea
from .utils.llm import llm_keywords_prompt

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    tab1, tab2 = st.tabs(["Keyword", "TBD"])
    with tab1:
        # st.write(f"Paper Name: {paper_name}, Username: {username}")
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve paper idea.")
            return
        keywords = paper_data['paper'].get('keywords', [])
        if not keywords:
            st.subheader("Setup keywords")
            def on_change_keywords():
                suggested_keywords = llm_keywords_prompt(
                    st.session_state["keywords_input_form"].split(",")
                )
                st.session_state['tipwords'] = suggested_keywords

            tmp_keywords_input = st.text_input(
                "Please enter keywords separated by commas 👇",
                value="",
                key="keywords_input_form",
                on_change=on_change_keywords,
            )
            if st.session_state.get('tipwords'):
                st.info("Suggested keywords: " + ", ".join(st.session_state['tipwords']))
            submit_button = st.button("Submit")
            if submit_button:
                keywords = [
                    keyword.strip() for keyword in tmp_keywords_input.split(",")
                ]
                update_paper_idea(paper_name, username, {"keywords": keywords})
                st.session_state.keywords = keywords
                st.success("Keywords updated successfully!")
                    
        else:
            st.subheader("Keywords")
            keywords = paper_data['paper'].get('keywords', [])
            st.write(", ".join(keywords))
            st.session_state.keywords = keywords