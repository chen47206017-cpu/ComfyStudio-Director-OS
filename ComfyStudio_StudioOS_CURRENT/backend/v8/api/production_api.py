
from flask import Blueprint,jsonify,request

from v8.engines.script_parser import parse_script

from v8.engines.continuity_manager import create_link


production_api=Blueprint(

"production_api",

__name__,

url_prefix="/api/v8/production"

)



@production_api.route("/parse",
methods=["POST"])

def parse():

    data=request.json or {}

    return jsonify(

    parse_script(
    data.get("text",""),
    data.get("episode","E01")
    )

    )



@production_api.route("/continuity",
methods=["POST"])

def continuity():

    data=request.json or {}

    return jsonify(

    create_link(
    data["previous"],
    data["next"]
    )

    )



