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
            with st.form(key='keywords_form'):
                st.session_state.keywords_input = st.text_input("Please enter keywords separated by commas 👇", value="", key="keywords_input_form")
                suggest_keywords_button = st.button("Suggest keywords")
                submit_button = st.form_submit_button(label='Submit')
                if st.session_state.keywords_input and suggest_keywords_button:
                    suggested_keywords = llm_keywords_prompt(st.session_state.keywords_input.split(","))
                    st.info(", ".join(suggested_keywords))
                if submit_button:
                    keywords = [keyword.strip() for keyword in st.session_state.keywords_input.split(',')]
                    # 更新關鍵字
                    update_paper_idea(paper_name, username, {"keywords": keywords})
                    st.session_state.keywords_input = ""
                    st.session_state.keywords = keywords
                    st.success("Keywords updated successfully!")
                    
        else:
            st.subheader("Keywords")
            keywords = paper_data['paper'].get('keywords', [])
            st.write(", ".join(keywords))
            st.session_state.keywords = keywords