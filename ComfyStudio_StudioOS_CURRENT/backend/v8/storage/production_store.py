
import json
import os


DB="database/v8/production.json"



def read_db():

    if not os.path.exists(DB):

        return {
        "projects":[],
        "episodes":[],
        "shots":[],
        "assets":[],
        "tasks":[]
        }


    with open(
    DB,
    "r",
    encoding="utf-8"
    ) as f:

        return json.load(f)




def write_db(data):

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




def add_shots(shots):

    data=read_db()

    data["shots"].extend(shots)

    write_db(data)

    return shots


