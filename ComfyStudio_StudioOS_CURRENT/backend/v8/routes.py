
from flask import Blueprint,jsonify,request

from v8.engines.canon_gate import check_canon

from v8.engines.prompt_compiler import build_prompt

from v8.api.comfy_router import health,submit



v8_api=Blueprint(
"v8_api",
__name__,
url_prefix="/api/v8"
)



@v8_api.route("/status")
def status():

    return jsonify({

    "version":"V8.2",

    "status":"running",

    "comfy":health()

    })




@v8_api.route("/canon/check",
methods=["POST"])
def canon():

    data=request.json or {}

    return jsonify(
    check_canon(data)
    )




@v8_api.route("/prompt/build",
methods=["POST"])
def prompt():

    data=request.json or {}

    return jsonify(
    build_prompt(data)
    )




@v8_api.route("/comfy/submit",
methods=["POST"])
def comfy():

    data=request.json or {}

    return jsonify(
    submit(data)
    )



