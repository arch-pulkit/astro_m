from fastapi import FastAPI
from pathlib import Path
import json
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

db_file = Path("database.json")




#when posting to /records, we tell web server to make it permanent on its backend
"""
in post record section what we are doing is loading the json file using path, 
storing it in another file as read only for checking if data exits or not; 
then appending the json model dump, then writing and finalising it
"""


@app.post("/records")
def create_record(record: Record):
    if db_file.exists():
        with open(db_file, "r") as file:
            try:
                data1 = json.load(file)
            except json.JSONDecodeError:
                data1 = []
    else:
        data1 = []

    data1.append(record.model_dump())

    with open(db_file, "w") as f:
        json.dump(data1, f, indent=4)

    return {"message": "Record saved successfully", "data": record}

@app.get("/records")
def get_records():
    if db_file.exists():
        with open(db_file, "r") as f:
            return json.load(f)
    return []

@app.get("/")
def root():
    return {"Status: OK"}