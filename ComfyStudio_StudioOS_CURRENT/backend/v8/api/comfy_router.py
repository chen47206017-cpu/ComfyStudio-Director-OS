
import requests


COMFY_URL="http://127.0.0.1:8189"



def health():

    try:

        r=requests.get(
        COMFY_URL,
        timeout=3
        )

        return {

        "connected":True,

        "status":r.status_code

        }


    except Exception as e:

        return {

        "connected":False,

        "error":str(e)

        }



def submit(workflow):

    r=requests.post(

    COMFY_URL+"/prompt",

    json=workflow,

    timeout=30

    )

    return r.json()

