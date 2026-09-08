
from flask import Blueprint,jsonify,request

from v8.swarm.manager import execute



swarm_api=Blueprint(

"swarm_api",

__name__,

url_prefix="/swarm"

)



@swarm_api.route(

"/run",

methods=["POST"]

)

def run():

    return jsonify(

    execute(request.json or {})

    )


@swarm_api.route(

"/status"

)

def status():

    return jsonify({

    "status":"running"

    })

