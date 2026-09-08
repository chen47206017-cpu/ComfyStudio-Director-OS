

import os


def scan_assets(root="assets"):


    result=[]


    if not os.path.exists(root):

        return result



    for path,dirs,files in os.walk(root):


        for f in files:


            result.append({

            "file":f,

            "path":
            os.path.join(path,f)

            })


    return result



