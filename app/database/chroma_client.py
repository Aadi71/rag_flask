import chromadb
from app.config import CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION_NAME

class ChromaDBClient:
    def __init__(self):
        try:
            self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            self.collection = self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME
            )
            print("✅ ChromaDB connection successful.")
        except Exception as e:
            print(f"🔥 Failed to connect to ChromaDB: {e}")
            self.client = None
            self.collection = None

    def get_collection(self):
        return self.collection

chroma_client = ChromaDBClient()
