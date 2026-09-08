
from flask import Blueprint,jsonify,request

from v8.voice.voice_qc import voice_check


voice_api=Blueprint(

"voice_api",

__name__,

url_prefix="/voice"

)


@voice_api.route(
"/check",
methods=["POST"]
)

def check():

    return jsonify(

    voice_check(

    request.json or {}

    )

    )


