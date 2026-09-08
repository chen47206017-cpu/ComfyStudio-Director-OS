
from flask import Blueprint,send_from_directory,jsonify


ui_api=Blueprint(
"ui_api",
__name__
)


@ui_api.route("/")
def home():

    return send_from_directory(
        "ui/v92",
        "director.html"
    )



@ui_api.route("/legacy")
def legacy():

    return send_from_directory(
        "ui",
        "index.html"
    )



@ui_api.route("/api/v8/ui/status")
def ui_status():

    return jsonify({

        "ui":"V9.2",

        "backend":"V9.1",

        "agent":True,

        "memory":True,

        "pipeline":True,

        "vision_qc":True

    })


