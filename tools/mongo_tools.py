import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))

SYSTEM_DBS = {"admin", "local", "config"}


def get_user_databases():
    try:
        dbs = [d for d in mongo_client.list_database_names() if d not in SYSTEM_DBS]
        if dbs:
            return dbs
    except Exception as e:
        print("⚠️ list_database_names failed:", e)
    try:
        uri = os.getenv("MONGO_URI", "")
        parsed = uri.split("/")[-1].split("?")[0].strip()
        if parsed and parsed not in SYSTEM_DBS:
            return [parsed]
    except Exception:
        pass
    return []


class MongoTools:

    @staticmethod
    def get_databases():
        user_dbs = get_user_databases()
        if not user_dbs:
            return "No user databases found."
        return "Available databases: " + ", ".join(user_dbs)

    @staticmethod
    def get_collections(database: str = None):
        if not database:
            dbs = get_user_databases()
            database = dbs[0] if dbs else None
        if not database:
            return "No database available."
        try:
            cols = mongo_client[database].list_collection_names()
        except Exception as e:
            return f"Could not list collections: {e}"
        if not cols:
            return f"No collections found in '{database}'."
        return f"Collections in '{database}': " + ", ".join(cols)

    @staticmethod
    def find_documents(database: str = None, collection: str = None, filters: dict = None, limit: int = 5):
        if not database:
            dbs = get_user_databases()
            database = dbs[0] if dbs else None
        if not collection:
            try:
                cols = mongo_client[database].list_collection_names()
                collection = cols[0] if cols else None
            except Exception:
                pass
        if not database or not collection:
            return "Could not determine database or collection."
        if filters is None:
            filters = {}
        try:
            docs = list(mongo_client[database][collection].find(filters, {"_id": 0}).limit(limit))
        except Exception as e:
            return f"Query failed: {e}"
        if not docs:
            return f"No documents found in '{database}.{collection}'."
        return f"Documents from '{database}.{collection}': {docs}"

    @staticmethod
    def count_documents(database: str = None, collection: str = None, filters: dict = None):
        if not database:
            dbs = get_user_databases()
            database = dbs[0] if dbs else None
        if not collection:
            try:
                cols = mongo_client[database].list_collection_names()
                collection = cols[0] if cols else None
            except Exception:
                pass
        if not database or not collection:
            return "Could not determine database or collection."
        if filters is None:
            filters = {}
        try:
            count = mongo_client[database][collection].count_documents(filters)
        except Exception as e:
            return f"Count failed: {e}"
        return f"Total documents in '{database}.{collection}': {count}"

    @staticmethod
    def search_all(keyword: str):
        results = []
        user_dbs = get_user_databases()
        for db_name in user_dbs:
            db = mongo_client[db_name]
            try:
                col_names = db.list_collection_names()
            except Exception:
                continue
            for col_name in col_names:
                col = db[col_name]
                for doc in col.find({}, {"_id": 0}).limit(100):
                    if keyword.lower() in str(doc).lower():
                        results.append({
                            "database": db_name,
                            "collection": col_name,
                            "match": doc
                        })
                        break
        if not results:
            return f"No documents found matching: '{keyword}'"
        return f"Search results for '{keyword}': {results}"
