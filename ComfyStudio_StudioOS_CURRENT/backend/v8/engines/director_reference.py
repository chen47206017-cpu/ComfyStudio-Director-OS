
import json
import os


DB="database/v8/references.json"



def create_reference(previous,next):


    data={

    "previous":previous,

    "next":next,

    "video_reference":

    previous+"_END5.mp4",


    "image_reference":

    previous+"_LAST.png"

    }


    items=[]


    if os.path.exists(DB):

        with open(DB,"r",encoding="utf8") as f:

            items=json.load(f)



    items.append(data)


    with open(
    DB,
    "w",
    encoding="utf8"
    ) as f:

        json.dump(
        items,
        f,
        ensure_ascii=False,
        indent=2
        )


    return data

