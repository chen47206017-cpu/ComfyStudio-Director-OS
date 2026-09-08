from flask import Flask,jsonify,request,send_from_directory
import json,os


ROOT=os.path.dirname(
os.path.dirname(
os.path.abspath(__file__)
)
)


DB=os.path.join(ROOT,"database")

UI=os.path.join(ROOT,"ui")



app=Flask(
__name__,
static_folder=UI,
static_url_path=""
)



def load(name):

    with open(
    os.path.join(DB,name),
    encoding="utf8"
    ) as f:

        return json.load(f)



def save(name,data):

    with open(
    os.path.join(DB,name),
    "w",
    encoding="utf8"
    ) as f:

        json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
        )



@app.route("/")
def index():

    return send_from_directory(
    UI,
    "index.html"
    )



@app.route("/api/shots")
def shots():

    return jsonify(
    load("shots.json")
    )



@app.route(
"/api/shots/save",
methods=["POST"]
)
def shot_save():

    save(
    "shots.json",
    request.json
    )

    return jsonify(
    {
    "status":"saved"
    }
    )



@app.route("/api/references")
def refs():

    return jsonify(
    load("references.json")
    )



@app.route("/api/queue")
def queue():

    return jsonify(
    load("queue.json")
    )



@app.route("/api/prompt/shot_compile",
methods=["POST"])
def prompt():

    shot=request.json

    return jsonify({

    "positive":
    "参考资产自动注入\n"+str(shot),

    "negative":
    "现代手机,错误年代,人物漂移"

    })



if __name__=="__main__":

    print(
    "ComfyStudio V3.4 DirectorOS"
    )

    app.run(
    host="127.0.0.1",
    port=8190
    )

