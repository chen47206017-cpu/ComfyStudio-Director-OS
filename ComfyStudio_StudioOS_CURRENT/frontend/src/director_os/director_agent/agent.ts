

export class DirectorAgent{


execute(
input:any
){



return {


received:true,


command:
input.command,


next:


[
"CHECK_CANON",
"LOAD_ASSETS",
"BUILD_PROMPT",
"RUN_MODEL",
"QC"

]



};



}



}



