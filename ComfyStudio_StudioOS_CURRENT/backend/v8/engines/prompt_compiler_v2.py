

def compile_prompt(shot):


    positive=[]


    if shot.get("scene"):

        positive.append(
        shot["scene"]
        )


    for c in shot.get(
    "characters",
    []
    ):

        positive.append(c)



    negative=[

    "年龄错误",

    "脸部漂移",

    "年代错误",

    "现代设备"

    ]



    return {

    "positive":
    "，".join(positive),


    "negative":
    "，".join(negative),


    "references":
    shot.get(
    "references",
    []
    )

    }


