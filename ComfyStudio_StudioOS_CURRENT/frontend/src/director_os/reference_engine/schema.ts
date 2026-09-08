
export type ReferenceType =

"CHARACTER"

|

"SCENE"

|

"PROP"

|

"VIDEO"


;


export interface ReferenceAsset{


id:string;


type:ReferenceType;


name:string;


path:string;


weight:number;


tags:string[];



}



export interface ReferencePack{


shotId:string;


assets:ReferenceAsset[];


inheritPrevious:boolean;



}


