
export interface ReferenceAsset{


id:string;


type:

"CHARACTER"

|

"SCENE"

|

"PROP"

|

"STYLE";


name:string;


source:string;


priority:number;


tags:string[];


}



export interface ShotReference{


shotId:string;


assets:ReferenceAsset[];


}


