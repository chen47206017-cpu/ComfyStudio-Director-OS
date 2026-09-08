
from flask import Blueprint,jsonify,request

from v8.agent.director_agent import run


agent_api=Blueprint(

"agent_api",

__name__,

url_prefix="/agent"

)



@agent_api.route(

"/run",

methods=["POST"]

)

def execute():

    return jsonify(

    run(request.json or {})

    )

