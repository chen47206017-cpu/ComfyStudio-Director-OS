
from flask import Blueprint,jsonify,request

from v8.api.swarm_api import swarm_api

from v8.api.agent_api import agent_api

from v8.api.memory_api import memory_api

from v8.api.vision_api import vision_api

from v8.api.voice_api import voice_api

from v8.api.continuity_api import continuity_api

from v8.api.audit_api import audit_api

from v8.api.production_pipeline_api import production_pipeline_api

from v8.api.director_api import director_api

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

    "version":"V8.2.1",

    "status":"running",

    "comfy":health()

    })



@v8_api.route("/canon/check",methods=["POST"])
def canon():

    return jsonify(
    check_canon(request.json or {})
    )



@v8_api.route("/prompt/build",methods=["POST"])
def prompt():

    return jsonify(
    build_prompt(request.json or {})
    )


@v8_api.route("/comfy/submit",methods=["POST"])
def comfy():

    return jsonify(
    submit(request.json or {})
    )




# ===== V8.3 Production Layer =====



# ===== END Production =====




# V8.3 Production routes

@v8_api.route(
'/production/parse',
methods=['POST']
)
def production_parse():

    from v8.engines.script_parser import parse_script

    data=request.json or {}

    return jsonify(
        parse_script(
            data.get('text',''),
            data.get('episode','E01')
        )
    )



@v8_api.route(
'/production/continuity',
methods=['POST']
)
def production_continuity():

    from v8.engines.continuity_manager import create_link

    data=request.json or {}

    return jsonify(
        create_link(
            data['previous'],
            data['next']
        )
    )





# ===== V8.3.2 Shot Persistence =====

@v8_api.route(
'/production/save',
methods=['POST']
)

def production_save():

    from v8.engines.script_parser import parse_script

    from v8.storage.production_store import add_shots


    data=request.json or {}


    shots=parse_script(
    data.get("text",""),
    data.get("episode","E01")
    )


    return jsonify(
    add_shots(shots)
    )


# ===== END Shot Persistence =====




# =================================
# V8.3.3 Production Verify
# =================================


@v8_api.route(
'/production/shots',
methods=['GET']
)

def production_shots():

    from v8.storage.production_store import read_db

    data=read_db()

    return jsonify(
    data.get('shots',[])
    )




@v8_api.route(
'/production/assets',
methods=['GET']
)

def production_assets():

    from v8.storage.production_store import read_db


    data=read_db()


    assets=data.get(
    'assets',
    []
    )


    return jsonify({

    'total':
    len(assets),

    'assets':
    assets

    })





@v8_api.route(
'/production/check',
methods=['POST']
)

def production_check():


    data=request.json or {}


    missing=[]


    required=data.get(
    'required_assets',
    []
    )


    from v8.storage.production_store import read_db


    db=read_db()


    assets=db.get(
    'assets',
    []
    )


    for item in required:

        if item not in assets:

            missing.append(item)



    return jsonify({

    'ready':
    len(missing)==0,

    'missing':
    missing

    })



# =================================
# END V8.3.3
# =================================




# ===== V8.4 Director API =====

v8_api.register_blueprint(
director_api
)

# ===== END Director =====




# ===== V8.5 Pipeline =====

v8_api.register_blueprint(
production_pipeline_api
)


# ===== END V8.5 =====




# ===== V8.5.1 Audit =====

v8_api.register_blueprint(
audit_api
)

# ===== END =====




# ===== V8.7 Continuity =====

v8_api.register_blueprint(
continuity_api
)

# ===== END =====




# ===== V8.95 Voice Memory =====

v8_api.register_blueprint(
voice_api
)

# ===== END Voice =====



# ===== V8.98 Vision QC =====

v8_api.register_blueprint(
vision_api
)

# ===== END Vision =====



# ===== V8.99 Memory =====

v8_api.register_blueprint(

memory_api

)

# ===== END Memory =====



# ===== V9 Director Agent =====

v8_api.register_blueprint(

agent_api

)

# ===== END Agent =====



# ===== V9.1 Swarm =====

v8_api.register_blueprint(

swarm_api

)

# ===== END Swarm =====

