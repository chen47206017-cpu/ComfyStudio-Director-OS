
from flask import Blueprint,send_from_directory,jsonify

import os


ui_root=Blueprint(
"ui_root",
__name__
)


@ui_root.route("/")
def home():


    return send_from_directory(

        os.path.join(

            os.getcwd(),

            "ui",

            "v92"

        ),

        "director.html"

    )



@ui_root.route("/legacy")
def legacy():


    return send_from_directory(

        os.path.join(

            os.getcwd(),

            "ui"

        ),

        "index.html"

    )



@ui_root.route("/api/ui/status")
def status():

    return jsonify({

        "ui":"V9.2",

        "status":"online",

        "backend":"V9.1",

        "agent":True,

        "memory":True,

        "pipeline":True

    })


