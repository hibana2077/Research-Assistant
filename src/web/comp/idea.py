import os
import requests
import streamlit as st
import streamlit_tags

from .utils.data import get_paper_idea, update_paper_idea
from .utils.llm import llm_keywords_prompt

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    st.subheader(f"Paper Name: {paper_name}")
    tab1, tab2 = st.tabs(["Keyword", "TBD"])
    with tab1:
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve paper idea.")
            return
        # Get current keywords if available
        keywords = paper_data['paper'].get('keywords', [])
        st.subheader("Keywords Setup")
        # Always show the text area, pre-populate if keywords exist
        tmp_keywords_input = st.text_area(
            "Please enter keywords separated by commas 👇",
            value=",".join(keywords) if keywords else "",
            key="keywords_input_form",
        )
        left_col, right_col = st.columns([1, 1])
        with right_col:
            generate_keywords = st.button("Generate Keywords", key="generate_keywords")
        with left_col:
            submit_button = st.button("Submit", key="submit_keywords")
        if generate_keywords:
            # Call the LLM to get suggested keywords
            st.session_state['tipwords'] = llm_keywords_prompt(tmp_keywords_input.split(","))
        if st.session_state.get('tipwords'):
            st.info("Suggested keywords: " + ", ".join(st.session_state['tipwords']))
        if submit_button:
            keywords = [keyword.strip() for keyword in tmp_keywords_input.split(",") if keyword.strip()]
            update_paper_idea(paper_name, username, {"keywords": keywords})
            st.session_state.keywords = keywords
            st.success("Keywords updated successfully!")
