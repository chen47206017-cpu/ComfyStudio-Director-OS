
import json
import os


DB="database/v8/continuity.json"



def link_previous(previous,next_shot):


    data={

    "previous":
    previous,


    "next":
    next_shot,


    "video_reference":
    previous+"_END5.mp4",


    "image_reference":
    previous+"_LAST.png"


    }


    save(data)


    return data




def save(data):

    os.makedirs(
    os.path.dirname(DB),
    exist_ok=True
    )


    old=[]


    if os.path.exists(DB):

        with open(DB,"r",encoding="utf8") as f:

            old=json.load(f)



    if not isinstance(old,list):

        old=[]


    old.append(data)


    with open(DB,"w",encoding="utf8") as f:

        json.dump(
        old,
        f,
        ensure_ascii=False,
        indent=2
        )


