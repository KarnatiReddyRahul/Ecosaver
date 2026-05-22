from pymongo import MongoClient

# Local MongoDB Connection
MONGO_URI = "mongodb://localhost:27017/"

def get_database():
    client = MongoClient(MONGO_URI)
    db = client["streamlit_app_db"]  # Database name
    return db
