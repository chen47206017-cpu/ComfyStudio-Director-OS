
import json
import os
import tempfile


def atomic_write(path,data):

    folder=os.path.dirname(path)

    os.makedirs(folder,exist_ok=True)

    fd,tmp=tempfile.mkstemp(dir=folder)

    with os.fdopen(fd,"w",encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp,path)



def read_json(path):

    if not os.path.exists(path):
        return {}

    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)

