
export interface ReferenceAsset{


id:string;


type:
"CHARACTER"|
"SCENE"|
"PROP"|
"STYLE";


name:string;


year:number;


priority:number;


role:string;


image:string;


}



export interface ReferenceValidation{


pass:boolean;


issues:string[];


}



