
export interface ScriptProject{


id:string;


title:string;


description:string;


episodes:Episode[];



}



export interface Episode{


id:string;


title:string;


summary:string;


shots:Shot[];



}



export interface Shot{


id:string;


scene:string;


year:number;


characters:string[];


props:string[];


emotion:string;


camera:string;


duration:number;



}



