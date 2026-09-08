

from flask import Blueprint,jsonify,request


from v8.storage.pipeline_store import load,save


production_pipeline_api=Blueprint(

"production_pipeline_api",

__name__,

url_prefix="/pipeline"

)



@production_pipeline_api.route(
"/status"
)

def status():

    return jsonify(
    load()
    )




@production_pipeline_api.route(
"/shot/create",
methods=["POST"]
)

def create_shot():


    data=request.json or {}


    db=load()


    db["shots"].append(data)


    save(db)


    return jsonify(data)




@production_pipeline_api.route(
"/queue"
)

def queue():

    return jsonify(
    load().get(
    "queue",
    []
    )
    )




