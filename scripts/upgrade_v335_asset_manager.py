import os
import json
from datetime import datetime


ROOT=r"F:\一人公司\comfyui-production"

APP=os.path.join(
ROOT,
"ComfyStudio_StudioOS_V3.3"
)

DB=os.path.join(
APP,
"database"
)


ASSET=os.path.join(
DB,
"assets.json"
)


REPORT=os.path.join(
ROOT,
"reports",
"comfystudio"
)


def save(path,data):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


print("="*60)
print("ComfyStudio V3.3B.5 Asset Manager")
print("="*60)



assets={


"version":"V3.3B.5",


"assets":[


{


"id":"CHAR_SW45_MASTER",

"name":"苏晚晴45岁",

"type":"character",


"preview":

"assets/characters/SW45.png",


"canon":

{

"year":2026,

"age":45,

"identity":"苏晚晴",

"face_lock":True,

"clothes_lock":True

},


"generation":

{

"reference":True,

"priority":1

},


"negative":

[

"年轻化",

"动漫化",

"双胞胎脸"

],


"tags":

[

"女主",

"空间设计师"

]


},



{


"id":"CHAR_SW25_MASTER",

"name":"苏晚晴25岁",

"type":"character",


"preview":

"assets/characters/SW25.png",


"canon":

{

"year":2006,

"age":25,

"identity":"苏晚晴"

},


"negative":

[

"45岁化"

]


},



{


"id":"SCENE_2006_STUDIO",

"name":"2006设计工作室",

"type":"scene",


"preview":

"assets/scenes/STUDIO2006.png",


"canon":

{

"year":2006,

"technology":

[

"有线电话",

"纸质设计稿"

]

},


"negative":

[

"现代手机",

"LED灯",

"现代家具"

]


},



{


"id":"PROP_PHONE_2006",

"name":"米黄色有线座机",

"type":"prop",


"preview":

"assets/props/PHONE2006.png",


"canon":

{

"year":2006,

"location":

"工作桌"

}

}


]


}



save(
ASSET,
assets
)



report={

"version":"V3.3B.5",

"status":"PASS",

"time":

datetime.now().isoformat()

}


save(

os.path.join(
REPORT,
"asset_manager_v335.json"
),

report

)


print()
print("ASSET_SCHEMA = PASS")
print("ASSET_MANAGER = READY")
print(ASSET)
