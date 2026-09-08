
export interface ReferenceAsset{


id:string;


type:
"CHARACTER"
|
"SCENE"
|
"PROP"
|
"VIDEO_FRAME";


path:string;


priority:number;


}



export interface ReferencePackage{


shotId:string;


year:number;


characterRefs:ReferenceAsset[];


sceneRefs:ReferenceAsset[];


propRefs:ReferenceAsset[];


videoRefs:ReferenceAsset[];


}



