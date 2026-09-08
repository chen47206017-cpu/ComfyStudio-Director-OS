
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


images:string[];


priority:number;


tags:string[];


}



export interface ReferencePack{


character?:ReferenceAsset[];


scene?:ReferenceAsset[];


props?:ReferenceAsset[];


style?:ReferenceAsset[];



}



