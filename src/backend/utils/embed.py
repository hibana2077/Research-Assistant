import os
import voyageai
import fastembed
import requests
import ollama
from openai import OpenAI
from fastembed import TextEmbedding

# Constants settings, read from environment variables
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "fastembed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_PROVIDER_API_KEY = os.getenv("EMBEDDING_PROVIDER_API_KEY", "your_embedding_provider_api_key")
EMBEDDING_PROVIDER_URL = os.getenv("EMBEDDING_PROVIDER_URL", "https://api.openai.com/v1/embeddings")
OLLAMA_SERVER = os.getenv("OLLAMA_SERVER", "http://localhost:11434")

def get_text_embedding(texts: list[str]) -> list[list[float]]:
    """
    Get text embeddings from the specified embedding provider.

    Args:
        texts (list[str]): List of texts to embed.

    Returns:
        list[list[float]]: List of embeddings for each text.
    """
    if EMBEDDING_PROVIDER == "openai":
        client = OpenAI(api_key=EMBEDDING_PROVIDER_API_KEY)
        response = client.embeddings.create(text=texts, model=EMBEDDING_MODEL).data[0].embedding
        return response
    
    elif EMBEDDING_PROVIDER == "voyageai":
        vo = voyageai.Client(api_key=EMBEDDING_PROVIDER_API_KEY)
        result = vo.embed(texts, model=EMBEDDING_MODEL, input_type="document")
        return result.embeddings # list[list[float]]

    elif EMBEDDING_PROVIDER == "fastembed":
        embed_model = TextEmbedding(model_name=EMBEDDING_MODEL, batch_size=32)
        embed_vector = list(embed_model.embed(texts,parallel=0)) # list[numpy.ndarray]
        return [vec.tolist() for vec in embed_vector] # list[list[float]]

    elif EMBEDDING_PROVIDER == "ollama":
        # ollama.embed(model='llama3.2', input=['The sky is blue because of rayleigh scattering', 'Grass is green because of chlorophyll'])
        model_list = ollama.list()
        if EMBEDDING_MODEL not in model_list:
            # warning: model not found, auto download
            ollama.pull(EMBEDDING_MODEL)
        client = ollama.Client(OLLAMA_SERVER)
        response = client.embed(model=EMBEDDING_MODEL, input=texts)
        return response.embeddings

    else:
        raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")