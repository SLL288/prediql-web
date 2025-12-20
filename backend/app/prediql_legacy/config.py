import os
from pathlib import Path

RUN_ID = os.getenv("PREDIQL_RUN_ID", "scratch")
RUN_ROOT = Path(os.getenv("PREDIQL_RUN_ROOT", "/app/runs"))
RUN_DIR = RUN_ROOT / RUN_ID
RUN_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    BASE_PATH = RUN_DIR
    GRAHPQLER_OUTPUT = BASE_PATH / "graphqler-output"
    MUTATION_FILE = GRAHPQLER_OUTPUT / "compiled" / "compiled_mutations.yml"
    QUERY_FILE = GRAHPQLER_OUTPUT / "compiled" / "compiled_queries.yml"
    ENDPOINTS_RESULTS = GRAHPQLER_OUTPUT / "endpoint_results"

    OUTPUT_DIR = BASE_PATH / "prediql-output"
    JSON_FILE = OUTPUT_DIR / "parsed_endpoint_data.json"
    TEXT_FILE = OUTPUT_DIR / "parsed_endpoint_text_data.txt"
    INDEX_FILE = OUTPUT_DIR / "parsed_endpoint_embedded_index.faiss"
    MODEL_NAME_FILE = OUTPUT_DIR / "model_name.txt"
    MODEL_NAME = "all-MiniLM-L6-v2"
