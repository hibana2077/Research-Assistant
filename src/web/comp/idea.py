import streamlit as st
import polars as pl

# from .utils.data import get_paper_idea, update_paper_idea
from .utils.data import (
    get_paper_idea,
    update_paper_idea,
    get_related_papers,
    get_vector_search,
)
from .utils.llm import llm_keywords_prompt

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    tab1, tab2, tab3 = st.tabs(["Keyword", "Related Papers", "Vector Search"])
    # Tab 1: Keywords
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
            value=", ".join(keywords) if keywords else "",
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
            st.session_state['tipwords'] = None
    # Tab 2: Related Papers
    with tab2:
        st.subheader("Related Papers")
        # Get data
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve related papers.")
            return
        keywords = paper_data['paper'].get('keywords', [])
        related_papers = paper_data['paper'].get('related_papers', [])

        # if keywords == none, "please enter keywords first"
        if not keywords:
            st.warning("Please enter keywords first.")
            return
        # Display related papers
        # if related_papers, display them
        # if not related_papers and keywords != none, "Please press the button to get related papers"
        if related_papers:
            st.write("Related Papers:")
            related_papers_df = pl.DataFrame(related_papers)
            st.dataframe(related_papers_df)
        elif related_papers == [] and keywords == []:
            st.warning("Please enter keywords first.")
        else:
            st.warning("Please press the button to get related papers.")

        # Button to get related papers
        get_related_papers_btn = st.button("Get Related Papers", key="get_related_papers")
        if get_related_papers_btn:
            # Call the LLM to get related papers
            related_papers = get_related_papers(keywords)
            if related_papers['status'] == 'fail':
                st.error("Failed to retrieve related papers.")
            else:
                # Update the paper idea with the new related papers
                update_paper_idea(paper_name, username, {"related_papers": related_papers['papers']})
                st.success("Related papers updated successfully!")
                # Display the related papers in a table
                related_papers_df = pl.DataFrame(related_papers['papers'])
                st.dataframe(related_papers_df)
    # Tab 3: Vector Search
    with tab3:
        st.subheader("Vector Search")
        # Get data
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve vector search.")
            return
        keywords = paper_data['paper'].get('keywords', [])
        vector_search = paper_data['paper'].get('vector_search', []) #collection nam, length should be 2, ['abstract_vec_timstamp', 'fulltext_vec_timestamp']

        # if keywords == none, "please enter keywords first"
        if not keywords:
            st.warning("Please enter keywords first.")
            return
        # Display vector search
        # if vector_search, display them
        # if not vector_search and keywords != none, "Please press the button to get vector search"
        if vector_search:
            st.write("Vector Search:")
            st.json(vector_search)
        elif vector_search == [] and keywords == []:
            st.warning("Please enter keywords first.")
        else:
            st.warning("Please press the button to get vector search.")

        # Button to get vector search
        get_vector_search_btn = st.button("Get Vector Search", key="get_vector_search")
        