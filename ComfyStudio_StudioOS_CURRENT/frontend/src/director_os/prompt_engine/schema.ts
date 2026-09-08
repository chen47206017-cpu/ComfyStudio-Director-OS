
export interface PromptShot{


episode:string;

shot:string;


year:number;


scene:string;


characters:string[];


props:string[];


references:string[];


action:string;


camera:string;


lighting:string;


dialogue:string;



}



export interface CompiledPrompt{


seedance:string;


comfyui:string;


constraints:string[];


}



