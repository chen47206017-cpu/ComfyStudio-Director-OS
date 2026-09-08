
export interface QCResult{


pass:boolean;


level:
"PASS"|
"WARNING"|
"FAILED";


issues:string[];


}



export interface QCContext{


year:number;


character:string[];


scene:string;


props:string[];


prompt:string;


}



