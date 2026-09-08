
from flask import Blueprint,jsonify,request


from v8.storage.director_store import load,save

from v8.engines.director_reference import create_reference



director_api=Blueprint(

"director_api",

__name__,

url_prefix="/director"

)



@director_api.route("/canvas")

def canvas():

    return jsonify(
    load()
    )



@director_api.route(
"/canvas/save",
methods=["POST"]
)

def canvas_save():

    return jsonify(
    save(
    request.json or {}
    )
    )



@director_api.route(
"/reference/link",
methods=["POST"]
)

def reference():

    data=request.json or {}

    return jsonify(

    create_reference(

    data.get("previous"),

    data.get("next")

    )

    )



@director_api.route("/assets")

def assets():

    return jsonify([

    {
    "id":"SW25",
    "type":"character",
    "name":"苏晚晴25岁"
    },

    {
    "id":"SW45",
    "type":"character",
    "name":"苏晚晴45岁"
    },

    {
    "id":"CN40",
    "type":"character",
    "name":"陈念40岁"
    },

    {
    "id":"STUDIO2006",
    "type":"scene",
    "name":"2006设计工作室"
    },

    {
    "id":"PHONE2006",
    "type":"prop",
    "name":"米黄色有线座机"
    }

    ])



