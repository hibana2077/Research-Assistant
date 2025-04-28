import os
import json
from openai import OpenAI

OPENROUTE_BASE_URL = os.getenv("OPENROUTE_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY", "your_openroute_api_key")
KEY_PROMPT_MODEL = os.getenv("KEY_PROMPT_MODEL", "gpt-3.5-turbo")

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