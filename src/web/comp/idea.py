import streamlit as st
import polars as pl

# from .utils.data import get_paper_idea, update_paper_idea
from .utils.data import (
    get_paper_idea,
    update_paper_idea,
    get_related_papers,
    get_emb_index,
    get_emb_col_info,
    similarity_search
)
from .utils.llm import (
    llm_keywords_prompt,
    llm_paper_title_prompt,
    llm_abstract_prompt,
    llm_novelty_check,
    llm_hypotheses_prompt,
    llm_experiment_design_prompt
)

@st.dialog("View Paper Idea")
def view_paper_dialog(paper_name, username):
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Keyword", "Related Papers", "Embedding", "Scaffolding Generator", "Paper Generate"])
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
            data = []
            for index in emb_index:
                collection_info = get_emb_col_info(index)
                points_count = collection_info.get("points_count", 0)
                data.append({"Collection Name": index, "points_count": points_count})
            df = pl.DataFrame(data)
            st.dataframe(df)
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

    # Tab 4: Generator
    with tab4:
        st.subheader("Generator")
        # Get data
        paper_data = get_paper_idea(paper_name, username)
        if paper_data['status'] == 'fail':
            st.error("Failed to retrieve paper idea.")
            return
        emb_index = paper_data['paper'].get('emb_index', [])
        # if emb_index == none, "please press the button to get Embedding"
        if not emb_index:
            st.warning("Please finish the previous step first.")
            return
        
        st.session_state['keywords'] = paper_data['paper'].get('keywords', [])
        generator_data = paper_data['paper'].get('generator', {})
        
        # paper generator steps
        ## 1. Describe the way(like TL;DR section and paper title)(here can use llm to generate that based on keywords)
        st.subheader("Describe the way")
        paper_title = st.text_input(
            "Please enter the title of the paper",
            value=generator_data.get('paper_title', ""),
            key="paper_title_input_form",
        )
        abstract = st.text_area(
            "Please enter the TL;DR section of the paper",
            value=generator_data.get('abstract', ""),
            key="tl_dr_input_form",
        )
        left_col, mid_col, right_col = st.columns([2, 1, 1])
        with left_col:
            suggest_paper_title = st.button("Suggest Paper Title", key="suggest_paper_title")
        with mid_col:
            suggest_abstract = st.button("Suggest TL;DR", key="suggest_abstract")
        with right_col:
            novelty_check = st.button("Novelty Check", key="novelty_check")
        save_section1 = st.button("Save", key="save_section1")
        if suggest_paper_title:
            relate_summaries_list = similarity_search(paper_name, username, ' '.join(st.session_state['keywords']))['results'][-1]
            relate_summaries = "\n".join([chunk['payload']['text'] for chunk in relate_summaries_list])
            # Call the LLM to get suggested paper title
            sg_paper_title = llm_paper_title_prompt(
                keywords=st.session_state['keywords'],
                user_draft_title=paper_title if paper_title else "",
                relate_summaries=relate_summaries
            )
            st.info(f"Suggested paper title: {sg_paper_title}")
        if suggest_abstract:
            relate_chunks_list = similarity_search(paper_name, username, ' '.join(st.session_state['keywords']))['results'][0]
            relate_chunks = "\n".join([chunk['payload']['text'] for chunk in relate_chunks_list])
            # Call the LLM to get suggested abstract
            sg_abstract = llm_abstract_prompt(
                keywords=st.session_state['keywords'],
                paper_title=paper_title if paper_title else "",
                relate_summaries=relate_chunks,
                user_draft_abstract=abstract if abstract else "",
            )
            st.info(f"Suggested Abstract: {sg_abstract}")
        if novelty_check:
            # Call the LLM to get novelty check
            # perplexity check -> summarize
            novelty_check_result = llm_novelty_check(
                paper_title=paper_title if paper_title else "",
                paper_abstract=abstract if abstract else "",
            )
            st.markdown("**Novelty Check Result**")
            st.markdown(f"Novelty: {novelty_check_result['novelty']}")
            st.markdown(f"Reason: {novelty_check_result['reason']}")
            st.markdown(f"Suggestion: {novelty_check_result['suggestion']}")
        if save_section1:
            paper_title = st.session_state.get('paper_title', paper_title)
            abstract = st.session_state.get('abstract', abstract)
            generator_data['paper_title'] = paper_title
            generator_data['abstract'] = abstract
            update_paper_idea(paper_name, username, {"generator": generator_data})
            st.session_state.paper_title = paper_title
            st.session_state.abstract = abstract
            st.success("Paper title and Abstract updated successfully!")
        ## 2. Proposal Hypothesis
        st.divider()
        st.subheader("Proposal Hypothesis")
        hypothesis = st.text_area(
            "Please enter your proposal hypothesis",
            value=generator_data.get('hypothesis', ""),
            key="hypothesis_input_form",
        )
        hypothesis_btn = st.button("Save", key="hypothesis_btn")
        suggest_hypothesis = st.button("Suggest Hypothesis", key="suggest_hypothesis")
        if hypothesis_btn:
            generator_data['hypothesis'] = hypothesis
            update_paper_idea(paper_name, username, {"generator": generator_data})
            st.session_state.hypothesis = hypothesis
            st.success("Proposal hypothesis updated successfully!")
        if suggest_hypothesis:
            # Call the LLM to get suggested hypothesis
            sg_hypothesis = llm_hypotheses_prompt(
                paper_title=st.session_state['paper_title'] if st.session_state.get('paper_title') else "",
                paper_abstract=st.session_state['abstract'] if st.session_state.get('abstract') else "",
            )
            # dict to polar dataframe
            st.json(
                body=sg_hypothesis,
                expanded=False
            )
            sg_hypothesis_df = pl.DataFrame(sg_hypothesis)
            st.dataframe(sg_hypothesis_df)
        ## 3. Generate Experiment structure (yaml)
        # -> let user can copy that and ask strongest code llm to generate code
        st.divider()
        st.subheader("Generate Experiment Structure")
        generate_experiment_structure_btn = st.button("Generate Experiment Structure", key="generate_experiment_structure")
        if generate_experiment_structure_btn:
            # Call the LLM to get suggested experiment structure
            experiment_structure_yaml = llm_experiment_design_prompt(
                paper_abstract=st.session_state['abstract'] if st.session_state.get('abstract') else "",
                paper_hypothesis=st.session_state['hypothesis'] if st.session_state.get('hypothesis') else "",
                paper_title=st.session_state['paper_title'] if st.session_state.get('paper_title') else "",
            )
            st.session_state['experiment_structure'] = experiment_structure_yaml
            # save to paper idea
            generator_data['experiment_structure'] = experiment_structure_yaml
            update_paper_idea(paper_name, username, {"generator": generator_data})
            st.success("Experiment structure updated successfully!")

        st.code(st.session_state.get('experiment_structure', ""), language="yaml")

    # Tab 5: Paper Generate
    with tab5:
        st.warning("This feature is work in progress.")