import sys
import os

BASE_DIR=os.path.dirname(os.path.abspath(__file__))

V8_DIR=os.path.dirname(BASE_DIR)

if V8_DIR not in sys.path:
    sys.path.insert(0,V8_DIR)


from flask import Flask,jsonify,send_from_directory,request

import os,json



ROOT=os.path.dirname(
os.path.dirname(
os.path.abspath(__file__)
)
)



UI=os.path.join(ROOT,"ui")

DB=os.path.join(ROOT,"database")



from routes.ui_root import ui_root

app=Flask(

__name__,

static_folder=UI,

static_url_path=""

)

# ===== V8 Production Core =====

from routes.v8_routes import v8_api

app.register_blueprint(v8_api)

# ===== END V8 =====





def load(name):

    with open(

    os.path.join(DB,name),

    encoding="utf8"

    ) as f:

        return json.load(f)








@app.route("/")

def index():

    return send_from_directory(

        "ui/v92",

        "director.html"

    )


@app.route("/legacy")

def legacy():

    return send_from_directory(

        "ui",

        "index.html"

    )

@app.route("/api/status")

def status():

    return jsonify({

    "version":"4.0",

    "name":"ComfyStudio Director Factory",

    "status":"running"

    })







@app.route("/api/assets")

def assets():

    return jsonify(

    load("studio.json")

    )







@app.route("/api/shots")

def shots():

    return jsonify(

    load("shots.json")

    )







@app.route("/api/canon")

def canon():

    return jsonify(

    load("canon.json")

    )







@app.route("/api/prompt",methods=["POST"])

def prompt():

    data=request.json


    return jsonify({

    "positive":

    "真人影视摄影\n"+str(data),


    "negative":

    "现代手机,LED灯,动漫化,年龄错误"

    })



if __name__=="__main__":

    print("======================")

    print("ComfyStudio V4.0")

    print("Director Factory")

    print("======================")


    app.run(

    host="127.0.0.1",

    port=8190

    )









@app.route("/api/reference")
def reference():

    return jsonify(
        load("reference.json")
    )









# ===== UTF8 JSON =====

app.config['JSON_AS_ASCII']=False

# ===== END UTF8 =====







# ===== V9.2 Director Studio UI =====


@app.route('/director')

def director_v92():

    return send_from_directory(

        'ui/v92',

        'director.html'

    )


# ===== END V9.2 =====





