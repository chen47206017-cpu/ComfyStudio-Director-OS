
import json
import os
import datetime


DB="database/v8/agent_tasks.json"


def load():

    if not os.path.exists(DB):

        return {
        "tasks":[],
        "history":[]
        }

    with open(DB,encoding="utf-8") as f:

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



def create_task(project,episode,goal):

    data=load()

    task={

    "project":project,

    "episode":episode,

    "goal":goal,

    "status":"PLANNED",

    "time":
    str(datetime.datetime.now())

    }


    data["tasks"].append(task)

    save(data)


    return task


