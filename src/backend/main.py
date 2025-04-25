import os
import json
import uvicorn
import pymongo
import numpy as np
import pandas as pd
from pprint import pprint
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# self-defined imports
from utils.arxiv import ArXivComponent

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
    pprint(result.inserted_id)
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
    paper_data = papers_collection.find_one({"paper_name": paper_name, "username": username, "_id": 0})
    
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
    query = query_data.get("query", "")
    arxiv = ArXivComponent(query=query, max_results=10)
    papers = arxiv.search_papers()
    
    if papers and "error" in papers[0]:
        raise HTTPException(status_code=400, detail=papers[0]["error"])
    
    return {"papers": papers}

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8081)