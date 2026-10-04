import json
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

#defining what the record looks like
#blueprint/ digital contract of the data
class Record(BaseModel):
    prompt: str
    response: str
    timestamp: str
    model_name: str


#not duplicating files or doing heavy file-to-file transfers.
#Instead treating Pydantic as an in-memory data filter.
#not loading the json file, but reading.
with open('fake_llm.json', 'r') as file:
    data = file.read()

the_dict = {}
"""
for d in data:
    if "prompt" == d:
        the_dict[d] = data[d] 

    if "response" == d:
        the_dict[d] = data[d]

    if "timestamp" == d:
        the_dict[d] = data[d]

    if "model_name" == d:
        the_dict[d] = data[d]
"""

try:
    user = Record.model_validate_json(data)
    #this dumps as a dict
    #for json, use model_dump_json()
    user1 = user.model_dump()
    print(user1)

except Exception as e:
    print("Validation failed: {e}")


#converting dict to json
json_string = json.dumps(the_dict, indent=4)

print(json_string)

app.post("/records")
def create_record(record: Record):
    return {"message": "Record saved successfully", "data": record}





