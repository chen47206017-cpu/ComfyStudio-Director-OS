
import json
import os


DB="database/v8/project_memory.json"



def load():

    if not os.path.exists(DB):

        return {}

    with open(DB,
    encoding="utf-8") as f:

        return json.load(f)



def save(data):

    with open(
    DB,
    "w",
    encoding="utf-8"
    ) as f:

        json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
        )


def search(keyword):

    data=load()

    result=[]

    text=json.dumps(
    data,
    ensure_ascii=False
    )

    if keyword in text:

        result.append(
        keyword
        )

    return result

