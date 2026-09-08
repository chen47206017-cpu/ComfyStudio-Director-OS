
def check_canon(shot):

    errors=[]


    year=shot.get("year")

    props=shot.get("props",[])


    if year=="2006":

        if "smartphone" in props:
            errors.append(
            "2006禁止出现智能手机"
            )


    return {

    "pass":len(errors)==0,

    "errors":errors

    }

