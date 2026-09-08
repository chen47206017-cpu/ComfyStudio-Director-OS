
export type ReferenceType=

"CHARACTER"
|
"SCENE"
|
"PROP"
|
"STYLE"
|
"SHOT";


export interface ReferenceAsset{


id:string;


type:ReferenceType;


name:string;


source:string;


priority:number;


tags:string[];


}



