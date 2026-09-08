
export interface PromptContext{


episode:string;


shot:string;


year:number;


character:string[];


scene:string;


props:string[];


emotion:string;


camera:string;


duration:number;


referencePack?:any;



}



export interface CompiledPrompt{


positive:string;


negative:string;


references:any;


}



