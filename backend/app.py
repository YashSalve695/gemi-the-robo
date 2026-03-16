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
MONGO_URI = os.getenv("MONGO_URI", "")

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
    allow_headers=["*"],
)

SYSTEM_DBS = {"admin", "local", "config"}


# ---------------------------
# DB Utilities
# ---------------------------

def get_user_databases():
    try:
        dbs = [d for d in mongo.list_database_names() if d not in SYSTEM_DBS]
        if dbs:
            return dbs
    except Exception as e:
        print("⚠️ list_database_names failed:", e)
    # Fallback: parse DB name from URI
    try:
        parsed = MONGO_URI.split("/")[-1].split("?")[0].strip()
        if parsed and parsed not in SYSTEM_DBS:
            return [parsed]
    except Exception:
        pass
    return []


def get_default_db():
    dbs = get_user_databases()
    return dbs[0] if dbs else None


def get_collections(db):
    try:
        cols = mongo[db].list_collection_names()
        print(f"📁 Collections in '{db}':", cols)
        return cols
    except Exception as e:
        print(f"⚠️ list_collection_names failed for '{db}':", e)
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
    try:
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
    except Exception as e:
        return f"Error fetching documents: {e}"


def db_count(db, col):
    try:
        count = mongo[db][col].count_documents({})
        return f"Total documents in '{db}.{col}': {count}"
    except Exception as e:
        return f"Error counting: {e}"


# ---------------------------
# Entity Detection
# ---------------------------

def detect_entities(question):
    q = question.lower()
    db = None
    col = None

    dbs = get_user_databases()
    for d in dbs:
        if d.lower() in q or d.lower().replace("_", "") in q.replace(" ", ""):
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

GEMINI_MODEL = "gemini-1.5-flash"


def ai_format(question, data):
    try:
        r = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"User Question:\n{question}\n\nDatabase Result:\n{data}\n\nExplain the answer clearly to the user.",
        )
        return r.text.strip()
    except Exception as e:
        print("⚠️ ai_format error:", e)
        return data


def ai_answer(question):
    try:
        r = gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Answer the following question clearly:\n{question}",
        )
        return r.text.strip()
    except Exception as e:
        print("⚠️ ai_answer error:", e)
        return f"Gemini error: {str(e)}"


# ---------------------------
# Router  (ORDER MATTERS — specific first, generic last)
# ---------------------------

def handle(question):
    q = question.lower()
    db, col = detect_entities(q)
    print("DB:", db, "COL:", col)

    # fallback to first collection
    if db and not col:
        cols = get_collections(db)
        if cols:
            col = cols[0]

    # 1. databases — check BEFORE documents ("database" contains "data")
    if any(w in q for w in ["database", "databases", "which db", "show db", "list db"]):
        return ai_format(question, db_databases())

    # 2. collections — check BEFORE documents
    if any(w in q for w in ["collection", "collections"]):
        return ai_format(question, db_collections(db))

    # 3. count
    if any(w in q for w in ["count", "how many", "total", "number of"]):
        if db and col:
            return ai_format(question, db_count(db, col))

    # 4. documents / records — most generic, must be LAST
    if any(w in q for w in
           ["record", "records", "document", "documents", "show", "get", "find", "fetch", "data", "user", "users"]):
        if db and col:
            return ai_format(question, db_documents(db, col, question))

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
    question = data.get("question", "").strip()
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
