

import {

ScriptProject

}

from "./schema";




export function analyzeScript(
input:any
){



const project:ScriptProject={


id:
"PROJECT_"+Date.now(),


title:
input.title,


description:
input.text,


episodes:[

]



};



return project;



}



