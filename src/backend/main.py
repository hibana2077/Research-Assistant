import os
import json
import time
import uvicorn
import logging
import pymongo
import tempfile
import numpy as np
import pandas as pd
from datetime import timezone
from pprint import pprint
from langchain_text_splitters import CharacterTextSplitter
from docling.document_converter import DocumentConverter
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

# self-defined imports
from utils.arxiv import ArXivComponent
from utils.download import download_arxiv_pdf
from utils.sse import make_sse_message
from utils.embed import get_text_embedding
from utils.pdf import is_valid_pdf
from utils.vectorstores import create_qd_collection, insert_qd_collection, search_qd_collection, get_collection_info

# self-defined config
from cfg.emb import FASTEMBED_MODELS, OPENAI_EMB_MODELS, VOYAGEAI_EMB_MODELS

# 常數設定，從環境變數中讀取設定
HOST = os.getenv("HOST", "127.0.0.1")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
MONGO_SERVER = os.getenv("MONGO_SERVER", "mongodb://localhost:27017")
MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "example")
OLLAMA_SERVER = os.getenv("OLLAMA_SERVER", "http://localhost:11434")
ACCLERATOR = os.getenv("ACCLERATOR", "cpu")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "fastembed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_PROVIDER_API_KEY = os.getenv("EMBEDDING_PROVIDER_API_KEY", "your_embedding_provider_api_key")
EMBEDDING_PROVIDER_URL = os.getenv("EMBEDDING_PROVIDER_URL", "https://api.openai.com/v1/embeddings")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# 設定SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB Database Setup
mongo_client = pymongo.MongoClient(
    MONGO_SERVER,
    username=MONGO_INITDB_ROOT_USERNAME,
    password=MONGO_INITDB_ROOT_PASSWORD
)
# ---

app = FastAPI()

# ---

# 使用者模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# 創建資料庫表格
Base.metadata.create_all(bind=engine)

# 依賴注入：資料庫會話
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 首頁路由
@app.get("/")
async def home():
    return {"message": f"Hello, World! {datetime.utcnow().isoformat()}"}

# Version check
@app.get("/version")
async def version():
    return {"version": "1.0.0"}

# 註冊路由
@app.post("/register")
async def register(user: dict, db: Session = Depends(get_db)):
    # 檢查使用者是否已存在
    existing_user = db.query(User).filter(User.username == user.get("username")).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # 創建新使用者
    new_user = User(username=user.get("username"), password=user.get("password"))
    db.add(new_user)
    
    try:
        db.commit()
        return {"status": "success", "message": "User registered successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed")

# 登入路由
@app.post("/login")
async def login(user: dict, db: Session = Depends(get_db)):
    # 查找使用者
    existing_user = db.query(User).filter(User.username == user.get("username")).first()
    
    # 驗證使用者
    if not existing_user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    if existing_user.password != user.get("password"):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    return {"status": "success", "message": "Login successful"}

# Create a new paper(collection) in MongoDB
@app.post("/papers/create")
async def create_paper(paper: dict):
    """
    Create a new paper in MongoDB.
    ## Structure:
    ```json
    {
        "paper_name": "paper_name", # static
        "username": "username", # static
    }
    ```
    """

    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    
    if not paper.get("paper_name") or not paper.get("username"):
        raise HTTPException(status_code=400, detail="Paper name and username are required")

    result = papers_collection.insert_one(paper)
    pprint(result)
    return {"status": "success", "message": "Paper created successfully"}

@app.post("/papers/update")
async def update_paper(paper: dict):
    """
    Update a paper in MongoDB.
    ## Structure:
    ```json
    {
        "paper_name": "paper_name",
        "username": "username",
        "new_data": {
            "key": "value"
        }
    }
    ```
    """
    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    
    paper_name = paper.get("paper_name")
    username = paper.get("username")
    if not paper_name or not username:
        raise HTTPException(status_code=400, detail="Paper name and username are required")
    new_data = paper.get("new_data", {})
    
    # Update the paper in MongoDB
    result = papers_collection.update_one({"paper_name": paper_name, "username": username}, {"$set": new_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {"status": "success", "message": "Paper updated successfully"}

@app.post("/papers/delete")
async def delete_paper(paper: dict):
    """
    Delete a paper in MongoDB.
    ## Structure:
    ```json
    {
        "paper_name": "paper_name",
        "username": "username"
    }
    ```
    """
    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    
    paper_name = paper.get("paper_name")
    username = paper.get("username")
    
    if not paper_name or not username:
        raise HTTPException(status_code=400, detail="Paper name and username are required")
    
    # Delete the paper in MongoDB
    result = papers_collection.delete_one({"paper_name": paper_name, "username": username})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {"status": "success", "message": "Paper deleted successfully"}

@app.post("/papers/list")
async def list_papers(data:dict):
    """
    List all papers in MongoDB.
    """
    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    
    papers = list(papers_collection.find({"username": data.get("username")}, {"_id": 0}))
    
    return {"status": "success", "papers": papers}

@app.post("/papers/get_one")
async def get_one_paper(paper: dict):
    """
    Get one paper in MongoDB.
    ## Structure:
    ```json
    {
        "paper_name": "paper_name",
        "username": "username"
    }
    ```
    """
    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    
    paper_name = paper.get("paper_name")
    username = paper.get("username")
    print(f"paper_name: {paper_name}, username: {username}")
    
    if not paper_name or not username:
        raise HTTPException(status_code=400, detail="Paper name and username are required")
    
    # Get the paper in MongoDB
    paper_data = papers_collection.find_one({"paper_name": paper_name, "username": username}, { "_id": 0})
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {"status": "success", "paper": paper_data}

@app.post("/arxiv/search")
async def search_arxiv(query_data: dict):
    """
    Search arXiv papers.
    ## Usage:
    ```bash
    curl -X POST "http://localhost:8081/arxiv/search" -H "Content-Type: application/json" -d '{"query":"graph neural networks, uncertainty quantification"}'
    ```
    """
    meta_query_list: list[str] = query_data.get("query", [])
    max_results: int = query_data.get("max_results", 5)
    query = ', '.join(list(keyword.strip() for keyword in meta_query_list))
    arxiv = ArXivComponent(search_query=query, max_results=max_results)
    papers = arxiv.search_papers()
    
    # logging
    logging.info(f"Searching arXiv for: {query}")
    logging.info(f"Found {len(papers)} papers:")

    if papers and "error" in papers[0]:
        raise HTTPException(status_code=400, detail=papers[0]["error"])
    
    return {"status": "success", "papers": papers}

async def create_embedding_event_generator(data:dict):
    """
    Create an embedding for the database.
    ```json
    {
        "paper_name": "paper_name",
        "username": "username"
    }
    ```
    """
    logging.info("Creating embedding...")
    # Load the paper data
    yield make_sse_message("Loading paper data...")
    paper_name = data.get("paper_name")
    username = data.get("username")
    if not paper_name or not username:
        raise HTTPException(status_code=400, detail="Paper name and username are required")
    yield make_sse_message("Loading paper data done.")
    

    logging.info(f"paper_name: {paper_name}, username: {username}")
    # Get the paper data from MongoDB
    yield make_sse_message("Loading paper data from MongoDB...")
    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    paper_data = papers_collection.find_one({"paper_name": paper_name, "username": username}, { "_id": 0})
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found")
    yield make_sse_message("Loading paper data from MongoDB done.")

    logging.info(f"Get related papers from MongoDB")
    # Get related papers
    yield make_sse_message("Loading related papers...")
    related_papers = paper_data.get("related_papers", [])
    if not related_papers:
        raise HTTPException(status_code=400, detail="No related papers found")
    yield make_sse_message("Loading related papers done.")
    
    # Download the related papers
    yield make_sse_message("Downloading related papers...")
    pdf_urls = [paper["pdf_url"] for paper in related_papers]
    temp_dir = tempfile.mkdtemp()
    logging.info(f"Temporary directory: {temp_dir}")
    for idx, pdf_url in enumerate(pdf_urls):
        yield make_sse_message(f"Downloading related paper {idx+1}/{len(pdf_urls)}...")
        download_arxiv_pdf(pdf_url, save_root_dir=temp_dir)
        time.sleep(0.78) # avoid too many requests
    yield make_sse_message("Downloading related papers done.")

    # Extract summary from related_papers
    yield make_sse_message("Extracting summary from related papers...")
    summaries = [] # list[str]
    for idx, paper in enumerate(related_papers):
        yield make_sse_message(f"Extracting summary from related paper {idx+1}/{len(related_papers)}...")
        summary = paper.get("summary", "")
        summaries.append(summary)
        time.sleep(1) # avoid too many requests
    yield make_sse_message("Extracting summary from related papers done.")

    # Using Docling to convert pdf to markdown
    yield make_sse_message("Converting pdf to markdown...")
    converter = DocumentConverter()
    markdowns = []
    # save markdown to temp dir
    md_tmp_dir = tempfile.mkdtemp()
    logging.info(f"Temporary markdown directory: {md_tmp_dir}")
    pdfs = [os.path.join(temp_dir, pdf) for pdf in os.listdir(temp_dir) if pdf.endswith(".pdf") and is_valid_pdf(os.path.join(temp_dir, pdf))] 
    for pdf in pdfs:
        yield make_sse_message(f"Converting {pdf} to markdown...")
        result = converter.convert(pdf)
        markdowns.append(result.document.export_to_markdown())
        # write to file
        with open(os.path.join(md_tmp_dir, os.path.basename(pdf) + ".md"), "w", encoding="utf-8") as f:
            f.write(markdowns[-1])
        logging.info(f"Saved markdown for {pdf} to {md_tmp_dir}")
    yield make_sse_message("Converting pdf to markdown done.")

    # Chunk
    yield make_sse_message("Chunking markdown...")
    if EMBEDDING_PROVIDER == "fastembed":
        chunk_size = next((int(it['context_length']) for it in FASTEMBED_MODELS if it['model'] == EMBEDDING_MODEL), 512)
        chunk_size = 2048 if chunk_size >= 2048 else chunk_size
        vector_size = next((int(it['dim']) for it in FASTEMBED_MODELS if it['model'] == EMBEDDING_MODEL), 768)
    elif EMBEDDING_PROVIDER == "openai":
        chunk_size = next((int(it['context_length']) for it in OPENAI_EMB_MODELS if it['model'] == EMBEDDING_MODEL), 2048)
        vector_size = next((int(it['dim']) for it in OPENAI_EMB_MODELS if it['model'] == EMBEDDING_MODEL), 1536)
    elif EMBEDDING_PROVIDER == "voyageai":
        chunk_size = next((int(it['context_length']) for it in VOYAGEAI_EMB_MODELS if it['model'] == EMBEDDING_MODEL), 16000)
        vector_size = next((int(it['dim']) for it in VOYAGEAI_EMB_MODELS if it['model'] == EMBEDDING_MODEL), 1536)
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="o200k_base", chunk_size=chunk_size, chunk_overlap=200
    )
    # for loop: chunking
    chuncked_markdowns = [] # List[List[str]]
    for idx, markdown in enumerate(markdowns):
        logging.info(f"Chunking {idx+1}/{len(markdowns)}...")
        yield make_sse_message(f"Chunking {idx+1}/{len(markdowns)}...")
        chunks = text_splitter.split_text(markdown)
        chuncked_markdowns.extend(chunks)
        time.sleep(0.78)
    
    logging.info(f"Chunking done. Total chunks: {len(chuncked_markdowns)}")
    yield make_sse_message(f"Chunking done. Total chunks: {len(chuncked_markdowns)}")
    
    # Create embedding(full paper)
    yield make_sse_message("Creating embedding...")
    full_paper_embeddings = []
    for idx, chunk in enumerate(chuncked_markdowns):
        
        logging.info(f"Creating embedding {idx+1}/{len(chuncked_markdowns)}...")
        yield make_sse_message(f"Creating embedding {idx+1}/{len(chuncked_markdowns)}...")
        
        start_time = time.time()
        embedding = get_text_embedding(chunk)
        full_paper_embeddings.append(embedding)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logging.info(f"Embedding {idx+1}/{len(chuncked_markdowns)} done. Elapsed time: {elapsed_time:.2f} seconds")
        yield make_sse_message(f"Creating embedding {idx+1}/{len(chuncked_markdowns)} done. Elapsed time: {elapsed_time:.2f} seconds")
    
    yield make_sse_message("Creating embedding done.")

    # Create embedding(summary)
    yield make_sse_message("Creating embedding for summary...")
    summary_embeddings = []
    for idx, summary in enumerate(summaries):
        yield make_sse_message(f"Creating embedding for summary {idx+1}/{len(summaries)}...")
        embedding = get_text_embedding(summary)
        summary_embeddings.append(embedding)
    yield make_sse_message("Creating embedding for summary done.")

    # Create Qdrant collection
    yield make_sse_message("Creating Qdrant collection...")
    full_paper_coll_name = f"full_paper_collection_{int(datetime.now(timezone.utc).timestamp())}"
    summary_coll_name = f"summary_collection_{int(datetime.now(timezone.utc).timestamp())}"
    # update to mongo
    papers_collection.update_one({"paper_name": paper_name, "username": username}, {"$set": {"emb_index": [full_paper_coll_name, summary_coll_name]}})
    # create qd_client and collection(full_paper)
    qd_client = create_qd_collection(QDRANT_URL, full_paper_coll_name, vector_size)
    logging.info(f"Full paper embedding length: {len(full_paper_embeddings)}")
    logging.info(f"Full paper chunked_markdowns length: {len(chuncked_markdowns)}")
    logging.info(f"Full paper embedding shape: {np.array(full_paper_embeddings).shape}") # (N, 1, 768) -> (N, 768)
    # convert to numpy array
    full_paper_embeddings = np.array(full_paper_embeddings).reshape(-1, vector_size)
    logging.info(f"Full paper embedding shape: {full_paper_embeddings.shape}") # (N, 768)
    # convert to list
    full_paper_embeddings = full_paper_embeddings.tolist()
    full_paper_saving_data = {
        "vectors": full_paper_embeddings,
        "payload": [{"text": chunk} for chunk in chuncked_markdowns]
    }
    # insert collection(full_paper) to qd_client
    insert_qd_collection(qd_client, full_paper_coll_name, full_paper_saving_data)
    # create qd_client and collection(summary)
    qd_client = create_qd_collection(QDRANT_URL, summary_coll_name, vector_size)
    logging.info(f"Summary embedding length: {len(summary_embeddings)}")
    logging.info(f"Summary embedding shape: {np.array(summary_embeddings).shape}") # (N, 1, 768) -> (N, 768)
    # convert to numpy array
    summary_embeddings = np.array(summary_embeddings).reshape(-1, vector_size)
    logging.info(f"Summary embedding shape: {summary_embeddings.shape}") # (N, 768)
    # convert to list
    summary_embeddings = summary_embeddings.tolist()
    summary_saving_data = {
        "vectors": summary_embeddings,
        "payload": [{"text": summary} for summary in summaries]
    }
    # insert collection(summary) to qd_client
    insert_qd_collection(qd_client, summary_coll_name, summary_saving_data)
    yield make_sse_message("Creating Qdrant collection done.")

    # Clean up
    for pdf in pdfs:
        os.remove(pdf)
    os.rmdir(temp_dir)
    yield make_sse_message("Clean up done.")

    yield make_sse_message("[DONE]")

    return

@app.get("/papers/get_emb_index")
async def get_emb_index(data: dict):
    """
    Get embedding index for a paper.
    ## Structure:
    ```json
    {
        "paper_name": "paper_name",
        "username": "username"
    }
    ```
    """
    return StreamingResponse(
        create_embedding_event_generator(data),
        media_type="text/event-stream",
    )

@app.get("/vec_store/col_count/{collection_name}")
async def get_collection_count(collection_name: str):
    """
    Get the count of a collection.
    """
    col_info = get_collection_info(QDRANT_URL, collection_name)
    return {"indexed_vectors_count": col_info.indexed_vectors_count,
            "optimizer_status": col_info.optimizer_status,
            "points_count": col_info.points_count,
            "segments_count": col_info.segments_count,
            "status": col_info.status,
            "vectors_count": col_info.vectors_count}

@app.post("/papers/similarity_search")
async def similarity_search(data: dict):
    """
    Perform similarity search for a given paper name and username.
    ## Structure:
    ```json
    {
        "paper_name": "paper_name",
        "username": "username",
        "query": "query"
    }
    ```
    """
    paper_name = data.get("paper_name")
    username = data.get("username")
    query = data.get("query")
    
    if not paper_name or not username or not query:
        raise HTTPException(status_code=400, detail="Paper name, username and query are required")
    
    # Get the paper data from MongoDB
    mongo_db = mongo_client["papers_db"]
    papers_collection = mongo_db["papers"]
    paper_data = papers_collection.find_one({"paper_name": paper_name, "username": username}, { "_id": 0})
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get the embedding index
    emb_index = paper_data.get("emb_index", [])
    
    if not emb_index:
        raise HTTPException(status_code=400, detail="No embedding index found")
    
    # Perform similarity search
    results = []
    for index in emb_index:
        result = search_qd_collection(QDRANT_URL, index, get_text_embedding([query])[0])
        results.append(result)
    
    return {"status": "success", "results": results} # len(results) = 2 

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8081)