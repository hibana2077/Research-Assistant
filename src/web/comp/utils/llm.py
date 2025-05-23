import os
import json
import logging
from openai import OpenAI

OPENROUTE_BASE_URL = os.getenv("OPENROUTE_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY", "your_openroute_api_key")
KEY_PROMPT_MODEL = os.getenv("KEY_PROMPT_MODEL", "openai/o3-mini")
TITLE_PROMPT_MODEL = os.getenv("TITLE_PROMPT_MODEL", "microsoft/phi-4-reasoning-plus")
ABSTRACT_PROMPT_MODEL = os.getenv("ABSTRACT_PROMPT_MODEL", "microsoft/phi-4-reasoning-plus")
NOVELTY_CHECK_MODEL = os.getenv("NOVELTY_CHECK_MODEL", "perplexity/sonar-reasoning-pro")
HYPOTHESES_PROMPT_MODEL = os.getenv("HYPOTHESES_PROMPT_MODEL", "openai/o3-mini")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/o3-mini")

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

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
    According to keywords and paper_title, ask LLM to generate a abstract related to the SCI field.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that suggests research paper abstracts in the scientific domain."
    user_prompt = (
        f"Given the research keywords: {', '.join(keywords)}, "
        f"and the research paper title: {paper_title}, "
        f"and the related summaries: {', '.join(relate_summaries)}, "
        f"and the user draft abstract: {user_draft_abstract}, "
        "please suggest one relevant research paper abstract. "
        "Reply with a JSON string only. "
        "e.g. {\"abstract\": \"...\"}"
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
            "abstract": content.strip()
        }
    return abstract["abstract"]

def llm_novelty_check(paper_title:str, paper_abstract:str) -> dict:
    """
    Check the novelty of a research paper by comparing its title and abstract with existing papers.
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
        f"and the research paper abstract: {paper_abstract}, "
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

def llm_hypotheses_prompt(paper_title:str, paper_abstract:str) -> list[dict]:
    """
    Generate a hypotheses based on the paper title and abstract.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You are an assistant that generates **research hypotheses** strictly aligned with the supplied paper's field (e.g., computer vision, graph learning)."
    user_prompt = (
        f"Given the research paper title: {paper_title}, "
        f"and the research paper abstract: {paper_abstract}, "
        "please propose 3 research hypotheses that directly build on this work. "
        "Return your answer in valid JSON, following exactly this schema:\n"
        "```\n"
        "{\n"
        '  "hypotheses": [\n'
        "    {\n"
        '      "name": "<concise hypothesis name>",\n'
        '      "description": "<2-3 sentence explanation>",\n'
        '      "verify_method": "<experimental or analytical method>",\n'
        '      "expected_result": "<what outcome would support the hypothesis>"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```"
    )

    # 呼叫 LLM
    response = client.chat.completions.create(
        model=HYPOTHESES_PROMPT_MODEL,
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
            "hypotheses": content.strip()
        }
    return result["hypotheses"] if isinstance(result, dict) else result

def llm_experiment_design_prompt(paper_title:str, paper_abstract:str, paper_hypotheses:str) -> str:
    """
    Generate an experiment design based on the paper title, abstract, and hypotheses.
    Return format: str.
    """
    # 初始化 client
    client = OpenAI(
        base_url=OPENROUTE_BASE_URL,
        api_key=OPENROUTE_API_KEY,
    )
    # 準備對話
    system_prompt = "You generate YAML experiment designs for scientific papers, specifying objectives, methods, data to collect, analyses, and metrics."
    user_prompt = (
        f"Given the research paper title: {paper_title}, "
        f"and the research paper abstract: {paper_abstract}, "
        f"and the research paper hypotheses: {paper_hypotheses}, "
        "please generate an experiment design and return in yaml format."
    )
    # 呼叫 LLM
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    logger.info(f"LLM response: {content}")
    # check if the response is in YAML format
    if content.startswith("```yaml") and content.endswith("```"):
        # remove ```yaml and ``` from the content
        content = content.replace("```yaml", "").replace("```", "")
    return content