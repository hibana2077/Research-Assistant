import httpx
from httpx_sse import connect_sse
import os
import json
import requests
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)

BACKEND_SERVER = os.getenv("BACKEND_SERVER", "http://localhost:8000")

def list_all_paper_idea(username):
    """
    List all paper ideas for a given username.
    """
    url = f"{BACKEND_SERVER}/papers/list"
    payload = {
        "username": username
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail", "papers": []}

def get_paper_idea(paper_name, username):
    """
    Get a paper idea by its name.
    """
    url = f"{BACKEND_SERVER}/papers/get_one"
    payload = {
        "paper_name": paper_name,
        "username": username
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail", "paper": {}}
    
def update_paper_idea(paper_name, username, new_data):
    """
    Update a paper idea by its name.
    """
    url = f"{BACKEND_SERVER}/papers/update"
    payload = {
        "paper_name": paper_name,
        "username": username,
        "new_data": new_data
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"status": "fail"}
    
def get_related_papers(keywords):
    """
    Get related papers based on keywords.
    """
    return_data = {
        "status": "fail",
        "papers": []
    }
    url = f"{BACKEND_SERVER}/arxiv/search"
    
    # 將關鍵字字串分割成列表，並包含原始關鍵字字串
    keyword_list = [keywords] + [k.strip() for k in keywords]
    for keyword in keyword_list:
        payload_list = {
            "query": keyword,
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload_list, headers=headers)
        logging.info(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return_data['status'] = 'success'
                return_data['papers'].extend(data['papers'])
            else:
                return_data['status'] = 'fail'
        else:
            return_data['status'] = 'fail'

    return return_data

def get_emb_index(paper_name: str, username: str):
    """
    Get embedding index for a paper using SSE with httpx.
    """
    url = f"{BACKEND_SERVER}/papers/get_emb_index"
    payload = {
        "paper_name": paper_name,
        "username": username
    }
    results = []
    try:
        # 使用 httpx.Client 建立連線
        with httpx.Client(timeout=None) as client: # timeout=None 避免長時間操作超時
            # 使用 connect_sse 建立 SSE 連線
            # httpx_sse 支援傳遞 json 參數
            with connect_sse(client, "GET", url, json=payload) as event_source:
                # 檢查 HTTP 狀態碼 (httpx_sse 會在連線失敗時拋出異常)
                # event_source.response.raise_for_status() # httpx_sse < 0.4.0
                # For httpx_sse >= 0.4.0, errors are raised during connect_sse

                # 迭代接收 SSE 事件
                for sse in event_source.iter_sse():
                    # sse.data 是每次 yield 的訊息字串
                    if sse.data == "[DONE]":
                        break
                    results.append(sse.data)
                    try:
                        # 嘗試解析 JSON 並顯示狀態
                        data = json.loads(sse.data)
                        status = data.get("status", "processing")
                        st.toast(status)
                    except json.JSONDecodeError:
                        # 如果不是 JSON，直接顯示原始訊息
                        st.toast(f"Received: {sse.data}")
                    except Exception as e:
                        st.error(f"Error processing event: {e}")
                        print(f"Error processing event data: {sse.data}, Error: {e}")

        return {"status": "success", "events": results}

    except httpx.RequestError as exc:
        st.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        return {"status": "fail", "events": [], "error": str(exc)}
    except httpx.HTTPStatusError as exc:
        st.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
        return {"status": "fail", "events": [], "error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return {"status": "fail", "events": [], "error": str(e)}
    
def get_emb_col_info(col_name: str):
    """
    Get embedding collection information.
    """
    url = f"{BACKEND_SERVER}/vec_store/col_count/{col_name}"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {"status": "success",
                "collection_name": col_name,
                **response.json()}
    else:
        return {"status": "fail",
            "collection_name": col_name,
            "indexed_vectors_count": 0,
            "optimizer_status": "unknown",
            "points_count": 0,
            "segments_count": 0,
            "status": "unknown",
            "vectors_count": 0}