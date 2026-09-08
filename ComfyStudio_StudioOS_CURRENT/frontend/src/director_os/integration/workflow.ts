
export interface DirectorWorkflow{


id:string;


episode:string;


shot:string;


nodes:string[];


status:string;


}


export const defaultDirectorFlow=[


"script",

"canon",

"character",

"scene",

"prop",

"reference",

"prompt",

"model",

"qc",

"delivery"


];



