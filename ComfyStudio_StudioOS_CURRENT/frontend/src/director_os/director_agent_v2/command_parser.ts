

export function parseCommand(
input:string
){



return {


project:
input,


action:
"CREATE_EPISODE",


steps:[

"LOAD_CANON",

"LOAD_ASSET",

"CREATE_SHOTS",

"BUILD_PROMPT",

"RUN_GENERATION",

"QC"

]



};



}



