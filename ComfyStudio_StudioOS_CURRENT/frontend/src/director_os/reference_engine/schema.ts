export interface ReferenceAsset{

id:string;

type:
"character" |
"scene" |
"prop";

name:string;

source:string;

image:string[];

priority:number;

locked:boolean;

}


export interface ReferenceValidation{

pass:boolean;

issues:string[];

}

