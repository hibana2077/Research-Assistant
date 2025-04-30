import pandas as pd
from fastembed import TextEmbedding
import re

temp_supported_models = (
    pd.DataFrame(TextEmbedding.list_supported_models())
    .sort_values("size_in_GB")
    .reset_index(drop=True)
)
temp_supported_models = temp_supported_models[["model", "description", "dim"]]
temp_supported_models["context_length"] = temp_supported_models["description"].apply(
    lambda x: re.search(r"(\d+)\s*input tokens truncation", x).group(1) if re.search(r"(\d+)\s*input tokens truncation", x) else x
)

FASTEMBED_MODELS = temp_supported_models.to_dict(orient="records")
# remove jinaai/jina-clip-v1 and jinaai/jina-embeddings-v3
FASTEMBED_MODELS = [
    model for model in FASTEMBED_MODELS if model["model"] not in ["jinaai/jina-clip-v1", "jinaai/jina-embeddings-v3"]
]
# [{'model': 'BAAI/bge-small-en-v1.5', 'context_length': '512', 'dim': 384},
#  {'model': 'BAAI/bge-small-zh-v1.5', 'context_length': '512', 'dim': 512},
#  {'model': 'snowflake/snowflake-arctic-embed-xs', 'context_length': '512', 'dim': 384},...]

OPENAI_EMB_MODELS = [
    {
        "model": "text-embedding-ada-002",
        "context_length": '8191',
        "dim": 1536
    },
    {
        "model": "text-embedding-3-small",
        "context_length": '8191',
        "dim": 1536
    },
    {
        "model": "text-embedding-3-large",
        "context_length": '8191',
        "dim": 3072
    }
]

VOYAGEAI_EMB_MODELS = [
    {
        "model": "voyage-3-large",
        "context_length": '32000',
        "dim": 1024
    },
    {
        "model": "voyage-3",
        "context_length": '32000',
        "dim": 1024
    },
    {
        "model": "voyage-3-lite",
        "context_length": '32000',
        "dim": 512
    }
]