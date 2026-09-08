import os
import shutil
from datetime import datetime



def backup():


    src=
    r"F:\一人公司\comfyui-production\ComfyStudio_StudioOS_CURRENT"


    dst=os.path.join(

        r"F:\一人公司\comfyui-production",

        "backup",

        datetime.now().strftime("%Y%m%d_%H%M%S")

    )


    os.makedirs(dst,exist_ok=True)


    for item in [

        "database",
        "assets",
        "workflows"

    ]:


        p=os.path.join(src,item)


        if os.path.exists(p):

            shutil.copytree(
                p,
                os.path.join(dst,item),
                dirs_exist_ok=True
            )


    return dst



if __name__=="__main__":

    print(
        backup()
    )

