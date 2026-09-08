
export type QCLevel =

"BLOCK" |

"WARNING" |

"PASS";



export interface QCResult{


level:QCLevel;


passed:boolean;


issues:string[];


}



export interface QCContext{


year:number;


character:string[];


scene:string;


props:string[];


references:any;


prompt:string;


}



