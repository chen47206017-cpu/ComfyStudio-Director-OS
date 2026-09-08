
import json
import os


DB="database/v8/shot_memory.json"


def save_memory(data):

    old={}

    if os.path.exists(DB):

        with open(DB,encoding="utf8") as f:
            old=json.load(f)


    old[data["shot"]]=data


    with open(DB,"w",encoding="utf8") as f:

        json.dump(
        old,
        f,
        ensure_ascii=False,
        indent=2
        )


    return data


def get_memory(shot):

    if not os.path.exists(DB):
        return {}

    with open(DB,encoding="utf8") as f:
        data=json.load(f)

    return data.get(shot,{})

