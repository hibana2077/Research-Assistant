import pandas as pd
from fastembed import TextEmbedding

temp_supported_models = (
    pd.DataFrame(TextEmbedding.list_supported_models())
    .sort_values("size_in_GB")
    .reset_index(drop=True)
)
temp_supported_models = temp_supported_models[["model", "description"]]
temp_supported_models["description"] = temp_supported_models["description"].apply(lambda x: x.split()[3])

FASTEMBED_MODELS = temp_supported_models.to_dict(orient="records")