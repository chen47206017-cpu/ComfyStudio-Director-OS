
import json
import os


DB="database/v8/canvas.json"



def load_canvas():

    if not os.path.exists(DB):

        return {
        "nodes":[],
        "edges":[]
        }


    with open(
    DB,
    "r",
    encoding="utf-8"
    ) as f:

        return json.load(f)



def save_canvas(data):

    os.makedirs(
    os.path.dirname(DB),
    exist_ok=True
    )


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


    return data

