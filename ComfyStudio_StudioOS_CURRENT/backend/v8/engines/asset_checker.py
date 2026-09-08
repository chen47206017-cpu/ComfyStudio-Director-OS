

def check_assets(shot,assets):


    missing=[]


    for a in shot.get(
    "required_assets",[]
    ):


        if a not in assets:

            missing.append(a)



    return {


    "ready":
    len(missing)==0,


    "missing":
    missing


    }


