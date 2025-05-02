import streamlit as st
import polars as pl

# from .utils.data import get_paper_idea, update_paper_idea
from .utils.data import (
    get_paper_idea,
    update_paper_idea,
    get_related_papers,
    get_emb_index,
    get_emb_col_info
)
from .utils.llm import llm_keywords_prompt

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Keyword", "Related Papers", "Embedding", "Generator", "Result"])
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
    # Tab 3: Embedding
    with tab3:
        st.subheader("Embedding Index")
        # Get data
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve Embedding Index.")
            return
        keywords = paper_data['paper'].get('keywords', [])
        emb_index = paper_data['paper'].get('emb_index', []) #collection nam, length should be 2, ['abstract_vec_timstamp', 'fulltext_vec_timestamp']

        # if keywords == none, "please enter keywords first"
        if not keywords:
            st.warning("Please enter keywords first.")
            return
        # Display Embedding
        # if emb_index, display them
        # if not emb_index and keywords != none, "Please press the button to get Embedding"
        if emb_index:
            st.write("Embedding:")
            # st.json(emb_index)# list of strings
            TABLE_TEXT = """| Collection Name | segments_count | points_count |\n|------------------|-----------------------|\n"""

            for index in emb_index:
                collection_info = get_emb_col_info(index)
                segments_count = collection_info.get("segments_count", 0)
                points_count = collection_info.get("points_count", 0)
                TABLE_TEXT += f"| {index} | {segments_count} | {points_count} |\n"
            st.markdown(TABLE_TEXT)
        elif emb_index == [] and keywords == []:
            st.warning("Please enter keywords first.")
        else:
            st.warning("Please press the button to get Embedding.")

        # Button to get Embedding
        get_emb_index_btn = st.button("Get Embedding", key="get_emb_index")
        if get_emb_index_btn:
            result = get_emb_index(paper_name=paper_name,
                                   username=username)
            status = result['status']
            if status == "success":
                st.success("Embedding updated successfully!")