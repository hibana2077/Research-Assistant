import os
import json
from openai import OpenAI

OPENROUTE_BASE_URL = os.getenv("OPENROUTE_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY", "your_openroute_api_key")
KEY_PROMPT_MODEL = os.getenv("KEY_PROMPT_MODEL", "gpt-3.5-turbo")
TITLE_PROMPT_MODEL = os.getenv("TITLE_PROMPT_MODEL", "microsoft/phi-4-reasoning-plus")
ABSTRACT_PROMPT_MODEL = os.getenv("ABSTRACT_PROMPT_MODEL", "microsoft/phi-4-reasoning-plus")
NOVELTY_CHECK_MODEL = os.getenv("NOVELTY_CHECK_MODEL", "perplexity/sonar-reasoning-pro")
HYPOTHESIS_PROMPT_MODEL = os.getenv("HYPOTHESIS_PROMPT_MODEL", "google/gemini-2.0-flash-001")

# 已設定：
# OPENROUTE_BASE_URL, OPENROUTE_API_KEY, KEY_PROMPT_MODEL

def llm_keywords_prompt(current_keywords: list[str]) -> list[str]:
    """
    根據 current_keywords，向 LLM 要求再建議 5 個與 SCI 領域有關的關鍵字。
    回傳格式：Python list of str。
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that suggests research keywords in the scientific domain."
    user_prompt = (
        f"Given the current research keywords: {', '.join(current_keywords)}, "
        "please suggest five additional relevant keywords related to scientific research. "
        "Reply with a JSON array of five strings only. "
        "e.g. [\"keyword1\", \"keyword2\", \"keyword3\", \"keyword4\", \"keyword5\"]"
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=KEY_PROMPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    
    # 將 JSON 字串解析回 Python list
    try:
        keywords = json.loads(content)
    except json.JSONDecodeError:
        # 若 LLM 回傳格式非 JSON，就嘗試以行拆分
        keywords = [
            line.strip("-  ").strip()
            for line in content.splitlines()
            if line.strip()
        ]
    return keywords

def llm_paper_title_prompt(keywords: list[str], user_draft_title: str, relate_summaries: list[str]) -> str:
    """
    Given keywords and user_draft_title, ask LLM to generate a paper title related to the SCI field.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that suggest research paper titles in the scientific domain."
    user_prompt = (
        f"Given the research keywords: {', '.join(keywords)}, user draft title: {user_draft_title}, "
        f"and the related summaries: {', '.join(relate_summaries)}, "
        "please suggest three relevant research paper title. "
        "Reply with a JSON array of three strings only. "
        "e.g. [\"title1\", \"title2\", \"title3\"]"
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=TITLE_PROMPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    # 將 JSON 字串解析回 Python list
    try:
        titles = json.loads(content)
    except json.JSONDecodeError:
        # 若 LLM 回傳格式非 JSON，就嘗試以行拆分
        titles = [
            line.strip("-  ").strip()
            for line in content.splitlines()
            if line.strip()
        ]
    return titles

def llm_abstract_prompt(keywords: list[str], paper_title: str, relate_summaries: list[str] = [], user_draft_abstract: str = "") -> str:
    """
    According to keywords and paper_title, ask LLM to generate a TL;DR related to the SCI field.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that suggests research paper TL;DRs in the scientific domain."
    user_prompt = (
        f"Given the research keywords: {', '.join(keywords)}, "
        f"and the research paper title: {paper_title}, "
        f"and the related summaries: {', '.join(relate_summaries)}, "
        f"and the user draft TL;DR: {user_draft_abstract}, "
        "please suggest one relevant research paper TL;DR. "
        "Reply with a JSON string only. "
        "e.g. {\"tl;dr\": \"...\"}"
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=ABSTRACT_PROMPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    # 將 JSON 字串解析回 Python dict
    try:
        abstract = json.loads(content)
    except json.JSONDecodeError:
        # 若 LLM 回傳格式非 JSON，就嘗試以行拆分
        abstract = {
            "tl;dr": content.strip()
        }
    return abstract["tl;dr"]

def llm_novelty_check(paper_title:str, paper_abstract:str) -> dict:
    """
    Check the novelty of a research paper by comparing its title and TL;DR with existing papers.
    Return format: dict.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that checks the novelty of research papers in the scientific domain."
    user_prompt = (
        f"Given the research paper title: {paper_title}, "
        f"and the research paper TL;DR: {paper_abstract}, "
        "please check the novelty of the paper and return a JSON object with the results."
        "e.g. {\"novelty\": \"1 to 10\", \"reason\": \"...\", \"suggestion\": \"...\"}"
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=NOVELTY_CHECK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    # 將 JSON 字串解析回 Python dict
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # 若 LLM 回傳格式非 JSON，就嘗試以行拆分
        # result example = ```json { "novelty": 4, "reason": "The core methodology of combining bootstrap aggregation (bagging) with Directed Acyclic Graphs (DAGs) was already introduced in the 2014 paper 'Learning directed acyclic graphs via bootstrap aggregating' [1], which proposed DAGBag for reducing false positives in edge detection via ensemble aggregation. The described paper's application to video/data representations appears contextually novel but builds directly on established principles of bagging (variance reduction in unstable models [2][3]) and existing DAG-specific implementations. The efficiency claims for high-dimensional scenarios align with prior computational optimizations in DAGBag [1].", "suggestion": "To enhance novelty, the authors could explore integration with modern ensemble techniques (e.g., stacking or boosting hybrids) or demonstrate unique topological constraints in video representation DAGs not addressed by general DAGBag frameworks. Comparisons against graph-based adaptations of random forests [2] would better contextualize improvements.", "references": ["1", "2", "3"] }```
        # remove ```json and ``` from the content
        content = content.replace("```json", "").replace("```", "")
        # 將 JSON 字串解析回 Python dict
        result = json.loads(content)
    return result

def llm_hypothesis_prompt(paper_title:str, paper_abstract:str) -> list[dict]:
    """
    Generate a hypothesis based on the paper title and abstract.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that generates research hypotheses in the scientific domain."
    user_prompt = (
        f"Given the research paper title: {paper_title}, "
        f"and the research paper Abstract: {paper_abstract}, "
        "please generate a hypothesis and return a JSON object with the results."
        "e.g. {\"hypothesis\": [hypothesis_obj_1, hypothesis_obj_2, ...], "
        "hypothesis_obj_n = {\"name\": \"...\", \"description\": \"...\", \"verify_method\": \"...\", \"expected_result\": \"...\"}"
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=HYPOTHESIS_PROMPT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    # 將 JSON 字串解析回 Python dict
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # 若 LLM 回傳格式非 JSON，就嘗試以行拆分
        result = {
            "hypothesis": content.strip()
        }
    return result["hypothesis"]

def llm_experiment_design_prompt(paper_title:str, paper_abstract:str, paper_hypothesis:str) -> str:
    """
    Generate an experiment design based on the paper title, abstract, and hypothesis.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that generates research experiment designs in the scientific domain."
    user_prompt = (
        f"Given the research paper title: {paper_title}, "
        f"and the research paper abstract: {paper_abstract}, "
        f"and the research paper hypothesis: {paper_hypothesis}, "
        "please generate an experiment design and return a JSON object with the results."
        "e.g. {\"experiment\": \"yaml format texts\"}"
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=NOVELTY_CHECK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    # 將 JSON 字串解析回 Python dict
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # 若 LLM 回傳格式非 JSON，就嘗試以行拆分
        result = {
            "experiment": content.strip()
        }
    return result["experiment"]