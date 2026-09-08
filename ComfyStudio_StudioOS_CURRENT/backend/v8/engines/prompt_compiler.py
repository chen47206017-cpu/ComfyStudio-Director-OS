
def build_prompt(shot):

    positive=[]

    negative=[]


    if shot.get("scene"):
        positive.append(
        shot["scene"]
        )


    if shot.get("character"):
        positive.append(
        shot["character"]
        )


    negative.extend([

    "年龄错误",

    "脸部漂移",

    "现代设备"

    ])


    return {

    "positive":"，".join(positive),

    "negative":"，".join(negative),

    "references":
    shot.get("references",[])

    }

