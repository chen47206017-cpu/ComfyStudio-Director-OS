import os
import sys
import json
import subprocess


BASE=os.path.dirname(
os.path.dirname(
os.path.abspath(__file__)
)
)



def check():


    result={}


    result["python"]={
        "status":"PASS",
        "version":sys.version
    }


    root="F:/一人公司/comfyui-production"


    studio=os.path.join(
        root,
        "ComfyStudio_StudioOS_CURRENT"
    )


    result["studio"]={

        "status":
        "PASS" if os.path.exists(studio)
        else "FAIL",

        "path":studio

    }


    try:

        gpu=subprocess.check_output(
            "nvidia-smi",
            shell=True
        ).decode(
            errors="ignore"
        )


        result["gpu"]={
            "status":"PASS",
            "info":gpu[:200]
        }


    except:


        result["gpu"]={
            "status":"UNKNOWN"
        }



    return result



if __name__=="__main__":

    print(
        json.dumps(
            check(),
            indent=2,
            ensure_ascii=False
        )
    )
