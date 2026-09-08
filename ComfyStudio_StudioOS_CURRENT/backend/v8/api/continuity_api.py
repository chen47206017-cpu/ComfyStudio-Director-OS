
from flask import Blueprint,jsonify,request

from v8.engines.shot_memory import save_memory,get_memory

from v8.engines.reference_builder import build_chain



continuity_api=Blueprint(

"continuity_api",

__name__,

url_prefix="/continuity"

)



@continuity_api.route(
"/save",
methods=["POST"]
)

def save():

    return jsonify(
    save_memory(request.json)
    )



@continuity_api.route(
"/build",
methods=["POST"]
)

def build():

    data=request.json

    return jsonify(
    build_chain(
    data["previous"],
    data["next"]
    )
    )


@continuity_api.route(
"/inherit/<shot>"
)

def inherit(shot):

    return jsonify(
    get_memory(shot)
    )


