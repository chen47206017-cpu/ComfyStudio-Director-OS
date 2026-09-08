import requests



def validate():


    result={}


    try:

        r=requests.get(
            "http://127.0.0.1:8190/api/status",
            timeout=3
        )


        result["api"]="PASS"


    except:


        result["api"]="FAIL"



    return result



if __name__=="__main__":

    print(validate())

