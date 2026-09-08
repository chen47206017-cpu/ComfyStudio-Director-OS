import os
import json
import shutil
from datetime import datetime


ROOT = r"F:\一人公司\comfyui-production"

OLD = os.path.join(
    ROOT,
    "ComfyStudio_Director_V3.2"
)

NEW = os.path.join(
    ROOT,
    "ComfyStudio_StudioOS_V3.3"
)


BACKUP = os.path.join(
    ROOT,
    "backups",
    "ComfyStudio_V3.3"
)


REPORT = os.path.join(
    ROOT,
    "reports",
    "comfystudio"
)


def mkdir(path):
    os.makedirs(
        path,
        exist_ok=True
    )


def write_json(path,data):

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
print("ComfyStudio StudioOS V3.3 Core Upgrade")
print("="*60)


# ==============================
# 1 Backup
# ==============================


mkdir(BACKUP)


if os.path.exists(OLD):

    shutil.copytree(
        OLD,
        os.path.join(
            BACKUP,
            "V3.2_backup"
        ),
        dirs_exist_ok=True
    )

    print(
        "BACKUP = PASS"
    )

else:

    print(
        "V3.2不存在，跳过备份"
    )



# ==============================
# 2 Create Runtime
# ==============================


dirs=[


"backend",

"database",

"ui",

"assets",

"assets/characters",

"assets/scenes",

"assets/props",

"assets/audio",

"assets/videos",

"workflows",

"reports"


]


for d in dirs:

    mkdir(
        os.path.join(
            NEW,
            d
        )
    )


print(
    "DIRECTORY = PASS"
)



# ==============================
# 3 Asset Registry
# ==============================


assets={


"version":"V3.3",


"assets":[


{

"id":"CHAR_SW45_MASTER",

"name":"苏晚晴45岁",

"type":"character",

"path":
"assets/characters/SW45.png",

"lock":[

"face",
"age",
"hair",
"clothes"

],

"negative":[

"年轻化",
"动漫化",
"双胞胎脸"

]


},


{

"id":"CHAR_SW25_MASTER",

"name":"苏晚晴25岁",

"type":"character",

"path":
"assets/characters/SW25.png",

"lock":[

"face",
"age"

]

},


{

"id":"CHAR_CN40_MASTER",

"name":"陈念40岁",

"type":"character",

"path":
"assets/characters/CN40.png"

},


{

"id":"SCENE_2006_STUDIO",

"name":"2006设计工作室",

"type":"scene",

"path":
"assets/scenes/STUDIO2006.png",

"negative":[

"现代手机",
"LED灯",
"现代家具"

]

},


{

"id":"PROP_PHONE_2006",

"name":"米黄色有线座机",

"type":"prop",

"path":
"assets/props/PHONE2006.png"

}


]


}



write_json(

os.path.join(
NEW,
"database",
"assets.json"
),

assets

)


print(
"ASSET_REGISTRY = PASS"
)



# ==============================
# 4 Canon Database
# ==============================


canon={


"version":"V3.3",


"rules":[


{

"name":"年代锁定",

"fields":[

"year",
"age",
"technology"

]

},


{

"name":"人物连续性",

"fields":[

"face",
"hair",
"clothes"

]

},


{

"name":"道具连续性",

"fields":[

"prop_state",
"location"

]

}


]


}


write_json(

os.path.join(
NEW,
"database",
"canon.json"
),

canon

)


print(
"CANON = PASS"
)



# ==============================
# 5 Canvas Database
# ==============================


canvas={


"nodes":[


{

"id":"CHAR_SW45_MASTER",

"type":"character",

"x":100,

"y":100


},


{

"id":"SHOT_E03_01",

"type":"shot",

"x":500,

"y":100


},


{

"id":"H3_GENERATOR",

"type":"generator",

"x":900,

"y":100


}


],


"edges":[


{

"source":"CHAR_SW45_MASTER",

"target":"SHOT_E03_01"

},


{

"source":"SHOT_E03_01",

"target":"H3_GENERATOR"

}


]


}



write_json(

os.path.join(
NEW,
"database",
"canvas.json"
),

canvas

)



print(
"CANVAS = PASS"
)



# ==============================
# Report
# ==============================


report={


"time":
datetime.now().isoformat(),


"version":"V3.3",


"path":NEW,


"status":"CORE_READY"


}


write_json(

os.path.join(
REPORT,
"V3.3_core_install.json"
),

report

)


print()
print("="*60)
print("ComfyStudio V3.3 CORE INSTALL PASS")
print("="*60)
print(NEW)