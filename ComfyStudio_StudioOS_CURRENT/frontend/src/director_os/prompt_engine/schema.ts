
export interface PromptContext{


shotId:string;


year:number;


characters:string[];


scene:string;


props:string[];


camera?:string;


duration?:number;


model?:string;


}



export interface CompiledPrompt{


positive:string;


negative:string;


model:string;


}



