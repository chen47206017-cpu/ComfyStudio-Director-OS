
export function parseProduction(
text:string
){


return {


command:"CREATE_EPISODE",


project:text,


pipeline:[

"CANON",

"ASSET",

"SHOT",

"PROMPT",

"MODEL",

"QUEUE",

"QC",

"EXPORT"


]


};


}


