import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient

load_dotenv()

# ---------------------------
# Setup
# ---------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

gemini = genai.Client(api_key=GEMINI_API_KEY)

mongo = MongoClient(MONGO_URI)

try:
    mongo.admin.command("ping")
    print("✅ MongoDB Connected")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

SYSTEM_DBS = {"admin", "local", "config"}

# ---------------------------
# DB Utilities
# ---------------------------

def get_user_databases():
    return [d for d in mongo.list_database_names() if d not in SYSTEM_DBS]


def get_default_db():
    dbs = get_user_databases()
    return dbs[0] if dbs else None


def get_collections(db):
    try:
        return mongo[db].list_collection_names()
    except Exception:
        return []


# ---------------------------
# Mongo Actions
# ---------------------------

def db_databases():
    dbs = get_user_databases()
    if not dbs:
        return "No databases found."
    return "Available databases: " + ", ".join(dbs)


def db_collections(db):

    if not db:
        db = get_default_db()

    if not db:
        return "No database available."

    cols = get_collections(db)

    if not cols:
        return f"No collections in '{db}'."

    return f"Collections in '{db}': " + ", ".join(cols)


def db_documents(db, col, question, limit=5):

    collection = mongo[db][col]

    sample = collection.find_one()

    query = {}

    if sample:

        q = question.lower()

        for field, value in sample.items():

            if field == "_id":
                continue

            if str(value).lower() in q:
                query[field] = value

    docs = list(collection.find(query, {"_id": 0}).limit(limit))

    if not docs:
        return f"No documents found in '{db}.{col}'."

    return f"Documents from '{db}.{col}': {docs}"


def db_count(db, col):

    count = mongo[db][col].count_documents({})

    return f"Total documents in '{db}.{col}': {count}"


# ---------------------------
# Entity Detection
# ---------------------------

def detect_entities(question):

    q = question.lower()

    db = None
    col = None

    dbs = get_user_databases()

    for d in dbs:
        if d.lower() in q or d.lower().replace("_","") in q.replace(" ",""):
            db = d
            break

    if not db:
        db = get_default_db()

    if db:
        cols = get_collections(db)

        for c in cols:
            if c.lower() in q:
                col = c
                break

    return db, col


# ---------------------------
# AI Formatting
# ---------------------------

def ai_format(question, data):

    try:

        r = gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
User Question:
{question}

Database Result:
{data}

Explain the answer clearly to the user.
"""
        )

        return r.text.strip()

    except Exception:
        return data


def ai_answer(question):

    try:

        r = gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
Answer the following question clearly:

{question}
"""
        )

        return r.text.strip()

    except Exception:

        return "Could not generate response."


# ---------------------------
# Router
# ---------------------------

def handle(question):

    q = question.lower()

    db, col = detect_entities(q)

    print("DB:", db, "COL:", col)

    # fallback collection
    if db and not col:
        cols = get_collections(db)
        if cols:
            col = cols[0]

    # documents
    if any(w in q for w in ["record","records","document","documents","data","user","users"]):

        if db and col:
            return ai_format(question, db_documents(db, col, question))

    # count
    if any(w in q for w in ["count","how many","number","total"]):

        if db and col:
            return ai_format(question, db_count(db, col))

    # collections
    if "collection" in q:

        return ai_format(question, db_collections(db))

    # databases
    if "database" in q or "db" in q:

        return ai_format(question, db_databases())

    return ai_answer(question)


# ---------------------------
# API
# ---------------------------

@app.get("/", response_class=HTMLResponse)
def home():

    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/ask")
async def ask(req: Request):

    data = await req.json()

    question = data.get("question","").strip()

    print("\nUSER:", question)

    if not question:
        return {"response": "Please ask a question."}

    try:

        resp = handle(question)

        print("RESP:", resp[:150])

        return {"response": resp}

    except Exception as e:

        print("ERROR:", e)

        return {"response": str(e)}