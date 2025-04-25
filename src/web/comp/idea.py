import os
import requests
import streamlit as st
import streamlit_tags

from utils.data import get_paper_idea

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    tab1, tab2 = st.tabs(["Keyword", "TBD"])
    with tab1:
        # keywords = get_paper_idea(paper_name)['paper']['keywords']
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve paper idea.")
            return
        keywords = paper_data['data'].get('keywords', [])
        if not keywords:
            st.subheader("Setup keywords")
            with st.form(key='keywords_form'):
                # keywords_input = st.text_input("Enter keywords (comma separated)")
                keywords_input = streamlit_tags.st_tags(
                    label="Enter keywords",
                    key="keywords_input",
                    default_value=keywords,
                    help_text="Press Enter to add a keyword",
                    placeholder="Type and press enter"
                )
                submit_button = st.form_submit_button(label='Submit')
                if submit_button:
                    keywords = [keyword.strip() for keyword in keywords_input.split(',')]
                    st.success("Keywords updated successfully!")
                    st.session_state.keywords = keywords
        else:
            st.subheader("Keywords")
            keywords = paper_data['data'].get('keywords', [])
            st.write(", ".join(keywords))
            st.session_state.keywords = keywords