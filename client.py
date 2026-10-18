from pydantic import BaseModel, ValidationError
import requests
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

"""
Every SDK method works this way, paired with a server endpoint:
SDK method (client.py)	        Sends over HTTP	            Server endpoint (app.py)	Runs in SQLite
save_record	                    POST /records	            create_record	            INSERT
clear_database	                DELETE /records/clear       clear_all_record	        DELETE
?	                            GET /records                get_records	                SELECT

"""

class RecordModel(BaseModel):
    prompt: str
    response: str
    timestamp: str
    model_name: str

astro_url = os.getenv("ASTRO_BASE_URL")

class AstroClient:
    def __init__(self, base_url= astro_url, timeout: float = 5.0):

        self.base_url = base_url.rstrip("/")

        #timeout stops the sdk from hanging forever if server never responds.
        self.timeout = timeout

    #single function to validate data using pydantic and post to backend
    #converts it to dict
    def save_record(self, prompt: str, response: str, model_name:str) -> dict:
            
        try:
            record = RecordModel(
                prompt=prompt,
                response=response,
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_name= model_name
            )
        #validation error means that the data was bad
        except ValidationError as e:
            return {"success": False, "error": f"Invalid record: {e}"}

        try:
            res = requests.post(f"{self.base_url}/records", json=record.model_dump(), timeout=self.timeout)

        except requests.RequestException as e:
            return {"success": False, "error": {e}}

        if res.status_code == 200:
            return{"success": True, "data":res.json()}

        return {"success": False, "status": res.status_code, "error": res.text}

    def clear_database(self) -> dict:
        try:
            res = requests.delete(f"{self.base_url}/records/clear", timeout=self.timeout )

        #requests.RequestException means the n/w or server failed
        except requests.RequestException as e:
            return {"success": False, "error": {e}}

        if res.status_code == 200:
            return {"success": True, "message": res.json().get("message")}
        else:
            return {"success": False, "status": res.status_code, "error": res.text}

    def get_records(self) -> dict:
        try:
            res = requests.get(f"{self.base_url}/records", timeout= self.timeout)
        except requests.RequestException as e:
            return {"success": False, "error": {e}}

        if res.status_code == 200:
            return {"success": True, "data": res.json()}
        else:
            return {"success": False, "status":res.status_code, "error": res.text}