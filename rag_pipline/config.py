import torch

class ImageDescriptionConfig:
    model_id = "microsfot/Florence-2-base"
    batch_size = 16
    device = "cuda" if torch.cuda.is_available() else "cpu"

class TableDescriptionConfig:
    model_id = "google/flan-t5-base"
    batch_size = 16
    device = "cuda" if torch.cuda.is_available() else "cpu"


class TextEmbeddingsConfig: 
    batch_size = 16
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = "BAAI/bge-small"
    model = "BAAI/bge-small"

class ImageEmbeddingsConfig:
    model = "clip"
