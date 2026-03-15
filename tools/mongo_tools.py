import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))

SYSTEM_DBS = {"admin", "local", "config"}

class MongoTools:

    @staticmethod
    def get_databases():

        dbs = mongo_client.list_database_names()

        user_dbs = [db for db in dbs if db not in SYSTEM_DBS]

        if not user_dbs:
            return "No user databases found."

        return "Available databases: " + ", ".join(user_dbs)

    @staticmethod
    def get_collections(database: str):

        db = mongo_client[database]

        cols = db.list_collection_names()

        if not cols:
            return f"No collections found in '{database}'."

        return f"Collections in '{database}': " + ", ".join(cols)

    @staticmethod
    def find_documents(database: str, collection: str, filters: dict=None, limit: int=5):

        if filters is None:
            filters = {}

        db = mongo_client[database]
        col = db[collection]

        docs = list(col.find(filters, {"_id": 0}).limit(limit))

        if not docs:
            return f"No documents found in '{database}.{collection}'."

        return f"Documents from '{database}.{collection}': {docs}"

    @staticmethod
    def count_documents(database: str, collection: str, filters: dict=None):

        if filters is None:
            filters = {}

        db = mongo_client[database]
        col = db[collection]

        count = col.count_documents(filters)

        return f"Total documents in '{database}.{collection}': {count}"

    @staticmethod
    def search_all(keyword: str):

        results = []

        db_names = mongo_client.list_database_names()

        user_dbs = [db for db in db_names if db not in SYSTEM_DBS]

        for db_name in user_dbs:

            db = mongo_client[db_name]

            for col_name in db.list_collection_names():

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