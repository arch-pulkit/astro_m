from pydantic import BaseModel
from pathlib import Path
import requests


def main():
    #defining what the record looks like
    #blueprint/ digital contract of the data
    #model schema
    class Record(BaseModel):
        prompt: str
        response: str
        timestamp: str
        model_name: str

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

main()


