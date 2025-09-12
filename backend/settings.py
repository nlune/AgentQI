from pydantic_settings import BaseSettings
import random
from pathlib import Path

# Correct root resolution
BACKEND_ROOT = Path(__file__).resolve().parent  # .../AgentQI/backend
REPO_ROOT = BACKEND_ROOT.parent                 # .../AgentQI

class Settings(BaseSettings):
    # db path anchored to backend directory
    db_path: Path = BACKEND_ROOT / "vector_db"
    
    # choose adapter modules
    vec_db: str = "chroma"
    spec_generator: str = "ollama"
    extractor: str = "ollama"
    doc_processor: str = "ocr"

    # model settings
    spec_gen_model: str = "llama3"  # "gpt-oss:20b"
    extraction_model: str = "llama3"
    temperature: float = 0.7

    # device settings
    device: str = "cpu"
    n_threads: int = 8
    n_gpu_layers: int = -1

    seed: int = random.randint(0, 1000000)
    extraction_specs_folder: Path = REPO_ROOT / "llm4qi" / "config" / "extraction_specs"

settings = Settings()