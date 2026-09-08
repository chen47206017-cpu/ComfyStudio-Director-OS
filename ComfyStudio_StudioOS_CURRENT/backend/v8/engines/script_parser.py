

def parse_script(text,episode):


    shots=[]


    lines=text.split("\n")


    index=1


    for line in lines:


        if line.strip():


            shots.append({

            "id":
            f"{episode}_SHOT{index:03}",

            "description":
            line,

            "status":
            "WAITING"

            })


            index+=1



    return shots



