

from flask import Blueprint,jsonify,request


audit_api=Blueprint(

"audit_api",

__name__,

url_prefix="/production"

)



@audit_api.route("/audit",
methods=["POST"])

def audit():


    data=request.json or {}


    result={

    "shot":
    data.get(
    "shot",
    "UNKNOWN"
    ),


    "canon":
    "PASS",


    "assets":
    "PASS",


    "reference":
    "READY",


    "voice":
    "CHECK"

    }


    return jsonify(result)



