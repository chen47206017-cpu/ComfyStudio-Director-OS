
export interface QCResult{


pass:boolean;


score:number;


errors:string[];


warnings:string[];


}



export interface ShotQCContext{


year:number;


characters:any[];


scene:any;


props:any[];


references:any;


prompt:string;



}



