
from flask import Blueprint,jsonify,request

from v8.memory.project_memory import search


memory_api=Blueprint(

"memory_api",

__name__,

url_prefix="/memory"

)


@memory_api.route(
"/search",
methods=["POST"]
)

def memory_search():

    data=request.json or {}

    return jsonify(

    {

    "query":
    data.get("query"),

    "memory":
    search(
    data.get("query","")
    )

    }

    )

