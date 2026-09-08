
export class OneClickRuntime{


async run(project:string){


return {


project,


pipeline:[


"CANON",

"ASSET",

"PROMPT",

"MODEL",

"QUEUE",

"GENERATION",

"QC",

"EXPORT"



],


status:"STARTED"



};



}



}



