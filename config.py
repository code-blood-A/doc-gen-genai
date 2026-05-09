import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
HF_TOKEN = os.getenv("HF_TOKEN")

# Paths
TARGET_REPO = os.getenv("TARGET_REPO")

# AI Settings
HF_INFERENCE_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-7B-Instruct"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "starcoder2:3b")
OLLAMA_FALLBACK = os.getenv("OLLAMA_FALLBACK", "True").lower() == "true"

# Parsing Settings
EXCLUDED_DIRS = {".git", "target", "build", ".idea", ".vscode", "docs"}
JAVA_EXT = ".java"

# Output Settings
DOCS_DIR = os.path.join(TARGET_REPO if TARGET_REPO else ".", "docs")

# Spring Annotations
SPRING_ANNOTATIONS = {
    "@RestController": "REST API layer - handles HTTP requests",
    "@Controller":     "MVC Controller layer",
    "@Service":        "Business logic layer",
    "@Repository":     "Data access layer - DB operations",
    "@Component":      "Generic Spring managed bean",
    "@Transactional":  "DB transaction management",
    "@Autowired":      "Dependency injection",
    "@RequestMapping": "URL route mapping",
    "@Entity":         "JPA database entity"
}
