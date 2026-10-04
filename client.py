import json


def main():
    with open('fake_llm.json', 'r') as file:
        data = json.load(file)

    the_dict = {}

    for d in data:
        if "prompt" == d:
            the_dict[d] = data[d] 

        if "response" == d:
            the_dict[d] = data[d]

        if "timestamp" == d:
            the_dict[d] = data[d]

        if "model_name" == d:
            the_dict[d] = data[d]

    print(the_dict)

    #converting dict to json
    json_string = json.dumps(the_dict, indent=4)

    print(json_string)


main()


