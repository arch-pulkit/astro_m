from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel
import sqlite3

app = FastAPI()

#defining what the record looks like
#blueprint/ digital contract of the data
class Record(BaseModel):
    prompt: str
    response: str
    timestamp: str
    model_name: str

#this way its easier to locate the file
#__file__ is path of app.py itself, so db always lives next to it
db_file = Path(__file__).parent / "database.db"

#Creating the SQLite file and table automatically if not exists.
def init_db():
    #connecting sqlite to db
    conn = sqlite3.connect(db_file)
    try:
        # Cursor object, a temp control structure & a bridge b/w Py application and SQLite db.
        #worker that travels through that pipeline to run commands nd fetch the data
        cursor = conn.cursor()

        #autoincrement is used to increase the id number each time, but it never reuses an id even after deletion
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

#initialiting the db table when server turns on
init_db()



#when posting to /records, we tell web server to make it permanent on its backend
"""
in post record section what we are doing is loading the json file using path, 
storing it in another file as read only for checking if data exits or not; 
then appending the json model dump, then writing and finalising it
"""

#NEW code entry with SQLite DB
#first start a connection, then create a cursor to make or see changes
#then execute these changes with cursor, then commit and close the conention
#in the link /docs, under records post, in responses loc tells what went wrong, where exactly the problem is

#try and finally gurantees conn.close() works even if execute raises an error
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
    finally:
        conn.close()

    return{"id": new_id,"data": record }

@app.get("/records")
def get_records():
    try:
        conn = sqlite3.connect(db_file)
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
    
