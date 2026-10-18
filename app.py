from fastapi import FastAPI, HTTPException
from pathlib import Path
from pydantic import BaseModel
import sqlite3
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

#fallback for db to local 

default_db = f"sqlite:///{Path(__file__).parent / 'database.db'}"
db_url = os.environ.get("ASTRO_DB_PATH", default_db)
db_file = db_url.replace("sqlite:///", "", 1)

class Record(BaseModel):
    prompt: str
    response: str
    timestamp: str
    model_name: str



def init_db():
    #connecting sqlite to db
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT,
                response TEXT,
                timestamp TEXT,
                model_name TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

#chaning when initializtion happens
#initialiting the db table when server turns on
#Lifespan lets FastAPI initlaize db when app starts, rather than when py imports app
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
app = FastAPI(lifespan=lifespan)


@app.post("/records")
def create_record(record: Record):
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()

        # ? placeholder in insert saves it from SQL injection; it meands sql treates it as data not SQL code
        cursor.execute(
            """
            INSERT INTO records (prompt, response, timestamp, model_name)
            VALUES (?, ?, ?, ?)
        """, 
            (record.prompt, record.response, record.timestamp, record.model_name)
        )
        conn.commit()
        new_id = cursor.lastrowid

    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=500, detail="Failed to save record",) from e
    finally:
        conn.close()

    return{"id": new_id,"data": record }

@app.get("/records")
def get_records():
    conn = sqlite3.connect(db_file)
    try:
        #Row function converts row tuples to Py dict automatically
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM records")
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]

@app.get("/")
def root():
    return {"Status": "OK"}

#every return is a dict with key and a value

@app.delete("/records/clear")
def clear_all_record():
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM records")

        # Reset the AUTOINCREMENT counter so IDs start at 1 again.
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='records'")

        conn.commit()
    finally:
        conn.close()
    return {"message": "data cleared"}
    
