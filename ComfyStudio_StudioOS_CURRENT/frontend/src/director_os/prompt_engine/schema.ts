
export interface PromptContext{


episode:string;


year:number;


character:string[];


scene:string[];


props:string[];


references:string[];


model:string;


}


export interface CompiledPrompt{


positive:string;


negative:string;


qc:string[];


}



