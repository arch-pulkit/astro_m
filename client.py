from pydantic import BaseModel, ValidationError
import requests
from datetime import datetime, timezone

"""
Every SDK method works this way, paired with a server endpoint:
SDK method (client.py)	        Sends over HTTP	            Server endpoint (app.py)	Runs in SQLite
save_record	                    POST /records	            create_record	            INSERT
clear_database	                DELETE /records/clear       clear_all_record	        DELETE
?	                            GET /records                get_records	                SELECT

"""

#no print in sdk, only return functions.

#defining what the record looks like
#blueprint/ digital contract of the data
#model schema
class RecordModel(BaseModel):
    prompt: str
    response: str
    timestamp: str
    model_name: str

# we need try/except for no reply
# and status check for bad reply


#blueprint for creating objects
#when building sdk using class, we are wrapping variables and functions into a single package
#makes code highly resuable
#first if the init and self, which is the constructor, which runs automatically exactly when you instantiate it
class AstroClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 5.0):

        self.base_url = base_url.rstrip("/")

        #timeout stops the sdk from hanging forever if server never responds.
        self.timeout = timeout

    #single function to validate data using pydantic and post to backend
    #converts it to dict
    def save_record(self, prompt: str, response: str, model_name:str) -> dict:
            
        try:
            #package and validate inputs using pydantic schema
            #calls the record model function, and adds the inputs from the argument to the rhs
            #time as utc timezone now
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
            #targetting the endpoint
            #url = f"{self.base_url}/records"
            # duming the above set data in it, and adding to the url
            res = requests.post(f"{self.base_url}/records", json=record.model_dump(), timeout=self.timeout)

        except requests.RequestException as e:
            return {"success": False, "error": {e}}

        if res.status_code == 200:
            return{"success": True, "data":res.json()}

        return {"success": False, "status": res.status_code, "error": res.text}

    def clear_database(self) -> dict:
        #function to delete
        #it sends a msg over HTTP to delete /records/clear
        #actual deletion happens in app.py clear_all_records where it deletes the entire sql db
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

"""

    db_file = Path("database.db")


    #not duplicating files or doing heavy file-to-file transfers.
    #Instead treating Pydantic as an in-memory data filter.
    #not loading the json file, but reading.

    try:
        with open('fake_llm.json', 'r') as file:
            data = file.read()
        user = Record.model_validate_json(data)
    except Exception as parse_err:
        print(f"Parse error, {parse_err}")
        exit()



    URL = "http://127.0.0.1:8000/records"

    try:
        #this dumps as a dict
        #for json, use model_dump_json()
        user1 = user.model_dump()
        print(user1)
        response = requests.post(URL, json=user1)
        print(response.status_code)

        if response.status_code == 200:
            print(response.json())
        else:
            print("failure")

    except Exception as e:
        print(f"Validation failed: {e}")


    #converting dict to json
    #user_json = user.model_dump_json()
    #print(user_json)



"""