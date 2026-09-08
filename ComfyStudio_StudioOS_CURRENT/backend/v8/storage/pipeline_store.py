

import json
import os


DB="database/v8/pipeline.json"



def load():


    if not os.path.exists(DB):

        return {

        "episodes":[],

        "shots":[],

        "queue":[]

        }



    with open(
    DB,
    "r",
    encoding="utf8"
    ) as f:

        return json.load(f)




def save(data):


    with open(
    DB,
    "w",
    encoding="utf8"
    ) as f:


        json.dump(

        data,

        f,

        ensure_ascii=False,

        indent=2

        )


    return data



