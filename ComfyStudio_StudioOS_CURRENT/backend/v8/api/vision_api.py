
from flask import Blueprint,jsonify,request

from v8.vision.vision_analyzer import analyze


vision_api=Blueprint(

"vision_api",

__name__,

url_prefix="/vision"

)



@vision_api.route(
"/check",
methods=["POST"]
)

def check():

    data=request.json or {}

    return jsonify(

    {

    "shot":

    data.get("shot"),

    "analysis":

    analyze(data)

    }

    )



@vision_api.route(
"/history"
)

def history():

    return jsonify([])

