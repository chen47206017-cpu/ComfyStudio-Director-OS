
import json
import os


DB="database/v8/reference_chain.json"


def build_chain(previous,next):

    data={}


    if os.path.exists(DB):

        with open(DB,encoding="utf8") as f:
            data=json.load(f)


    key=previous+"->"+next


    data[key]={

    "video":
    previous+"_END5.mp4",

    "frame":
    previous+"_LAST.png",

    "state":
    previous+"_STATE.json"

    }


    with open(DB,"w",encoding="utf8") as f:

        json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
        )


    return data[key]

