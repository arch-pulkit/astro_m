import json
from client import AstroClient

"""
sdk = astro_m(base_url="http://127.0.0.1:8000")


#first clearing old data for test
print("Wiping old data")
#need to use sdk. to access the class astro_m objects
clear_old = sdk.clear_database()
print("clear:", clear_old)


with open ("fake_llm.json" , "r") as f:
    raw_data = json.load(f)

#now trigerring the executon function
# parsing and saving the data to a variable
# the same name as the object stored" prompt" and searching and getting the data named "prompt"
result = sdk.save_record(
    prompt=raw_data.get("prompt"),
    response=raw_data.get("response"),
    timestamp=raw_data.get("timestamp"),
    model_name=raw_data.get("model_name")
)    

print(result)"""


"""
The full trip one record takes:
sdk_test.py: the prompts list gives "why do we work?".
fake_llm(prompt) returns "Fake answer to: why do we work?". That’s your response.
sdk.save_record(...), the SDK, adds the timestamp, validates the record and POSTs it.
app.py (POST /records) receives it, validates it again and runs INSERT into SQLite.
database.db stores it as a row with a new id.
GET /records reads the rows back. That’s the output you saw.
"""
def fake_llm(prompt: str) -> str:
    return f"Fake answer to: {prompt}" 

sdk = AstroClient()

print("clear:", sdk.clear_database())

prompts = ["why do we work?", "best theory of life"]

for prompt in prompts:
    response = fake_llm(prompt)
    result = sdk.save_record(prompt=prompt, response=response, model_name="bolty 2.3")
    print(result)


# we have to either store the method called, or use print statement to actually get the return statements
print()
print(sdk.get_records())