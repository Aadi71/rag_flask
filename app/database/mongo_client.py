from pymongo import MongoClient
from app.config import MONGO_URI, MONGO_DB_NAME, MONGO_LOG_COLLECTION
from app.models import LogEntry

class MongoLogger:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[MONGO_DB_NAME]
            self.collection = self.db[MONGO_LOG_COLLECTION]
            print("✅ MongoDB connection successful.")
        except Exception as e:
            print(f"🔥 Failed to connect to MongoDB: {e}")
            self.client = None

    def log(self, log_data: LogEntry):
        if self.client:
            self.collection.insert_one(log_data.dict())

mongo_logger = MongoLogger()
