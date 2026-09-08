
export function runEpisode(project:any){


return {


episode:
project.episode,


status:
"RUNNING",


pipeline:[


"CANON",

"ASSET",

"REFERENCE",

"PROMPT",

"MODEL",

"QUEUE",

"QC"



]


};



}



