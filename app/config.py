import os

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME = "academic-qa" # The name we'll give our custom model

# ChromaDB Configuration
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION_NAME = "research_papers"

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "rag_logs")
MONGO_LOG_COLLECTION = "query_logs"

# RAG Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# API Documentation
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
