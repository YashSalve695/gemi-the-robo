# ============================================================
# FIX_AND_RESTART.ps1
# Run this from:  C:\Users\Dell\Downloads\Gemi_The_Robo\
# Command:  .\FIX_AND_RESTART.ps1
# ============================================================

Write-Host "=== Step 1: Killing any running uvicorn processes ===" -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "=== Step 2: Clearing Python cache ===" -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "=== Step 3: Writing app.py directly ===" -ForegroundColor Yellow

$appPy = @'
import os
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI      = os.getenv("MONGO_URI")

gemini = genai.Client(api_key=GEMINI_API_KEY)
mongo  = MongoClient(MONGO_URI)

try:
    mongo.admin.command("ping")
    print("MONGO OK")
except Exception as e:
    print("MONGO FAIL:", e)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SYSTEM_DBS = {"admin", "local", "config"}

def db_databases():
    dbs = [d for d in mongo.list_database_names() if d not in SYSTEM_DBS]
    return ("Available databases: " + ", ".join(dbs)) if dbs else "No databases found."

def db_collections(database):
    cols = mongo[database].list_collection_names()
    return (f"Collections in '{database}': " + ", ".join(cols)) if cols else f"No collections in '{database}'."

def db_find(database, collection, limit=5):
    docs = list(mongo[database][collection].find({}, {"_id": 0}).limit(limit))
    return (f"Documents from '{database}.{collection}': {docs}") if docs else f"No documents in '{database}.{collection}'."

def db_count(database, collection):
    n = mongo[database][collection].count_documents({})
    return f"Total documents in '{database}.{collection}': {n}"

def db_search(keyword):
    out = []
    for db_name in mongo.list_database_names():
        if db_name in SYSTEM_DBS:
            continue
        for col in mongo[db_name].list_collection_names():
            for doc in mongo[db_name][col].find({}, {"_id": 0}).limit(200):
                if keyword.lower() in str(doc).lower():
                    out.append({"db": db_name, "col": col, "doc": doc})
                    break
    return (f"Results for '{keyword}': {out}") if out else f"Nothing found for '{keyword}'."

def ai_format(q, raw):
    try:
        r = gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Turn this MongoDB result into friendly plain English. No markdown.\nUser asked: {q}\nData: {raw}\nResponse:"
        )
        return r.text.strip()
    except:
        return str(raw)

def ai_answer(q):
    try:
        r = gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Answer clearly. No markdown.\nQuestion: {q}\nAnswer:"
        )
        return r.text.strip()
    except:
        return "Could not generate response."

def extract_db_col(q):
    m = re.search(r'\b(\w+)\.(\w+)\b', q)
    if m: return m.group(1), m.group(2)
    m = re.search(r'\b(?:in|from|of)\s+(\w+)\s+(\w+)', q)
    if m: return m.group(1), m.group(2)
    m = re.search(r'\b(?:in|from|of)\s+(\w+)', q)
    if m: return m.group(1), None
    return None, None

def handle(question):
    q = question.lower().strip()
    print(f"ROUTING: {q}")

    if any(w in q for w in ["database","databases","show db","list db","all db","what db","which db"]):
        return ai_format(question, db_databases())

    if any(w in q for w in ["collection","collections","tables"]):
        db, _ = extract_db_col(q)
        m = re.search(r'(?:collection|collections|tables)\s+(?:in|of|from)\s+(\w+)', q)
        if m: db = m.group(1)
        return ai_format(question, db_collections(db) if db else db_databases())

    if any(w in q for w in ["how many","count","total","number of"]):
        db, col = extract_db_col(q)
        if db and col: return ai_format(question, db_count(db, col))
        if db: return ai_format(question, db_collections(db))
        return ai_format(question, db_databases())

    if any(w in q for w in ["show","find","get","fetch","display","give","document","record","data","all","list"]):
        db, col = extract_db_col(q)
        if db and col: return ai_format(question, db_find(db, col))
        if db: return ai_format(question, db_collections(db))
        return ai_format(question, db_databases())

    if any(w in q for w in ["search","look for"]):
        stop = {"search","look","for","me","the","a","an","in","from","all","any"}
        kw = " ".join(w for w in q.split() if w not in stop).strip() or "data"
        return ai_format(question, db_search(kw))

    return ai_answer(question)

@app.get("/", response_class=HTMLResponse)
def home():
    with open("frontend/index.html","r",encoding="utf-8") as f:
        return f.read()

@app.post("/ask")
async def ask(req: Request):
    data = await req.json()
    question = data.get("question","").strip()
    print(f"\n{'='*50}\n[USER] {question}")
    if not question:
        return {"response": "Please ask a question."}
    try:
        resp = handle(question)
        print(f"[RESP] {resp[:150]}")
        return {"response": resp}
    except Exception as e:
        print(f"[ERR] {e}")
        return {"response": f"Error: {str(e)}"}
'@

Set-Content -Path "backend\app.py" -Value $appPy -Encoding UTF8
Write-Host "  backend\app.py written" -ForegroundColor Green

Write-Host "=== Step 4: Verifying old error message is GONE ===" -ForegroundColor Yellow
$check = Select-String -Path "backend\app.py" -Pattern "could not understand" -Quiet
if ($check) {
    Write-Host "  ERROR: Old file still present!" -ForegroundColor Red
} else {
    Write-Host "  CONFIRMED: New file is in place. Old error message gone." -ForegroundColor Green
}

Write-Host "=== Step 5: Starting uvicorn ===" -ForegroundColor Yellow
Write-Host "  Starting... open http://127.0.0.1:8000" -ForegroundColor Cyan
uvicorn backend.app:app --reload
'@