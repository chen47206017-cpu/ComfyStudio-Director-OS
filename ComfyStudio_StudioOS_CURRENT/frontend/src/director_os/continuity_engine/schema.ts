
export interface EntityState{


id:string;


type:
"CHARACTER"
|
"PROP"
|
"SCENE"
|
"DOOR";


owner?:string;


location?:string;


year:number;


status:string;


}


export interface ShotState{


episode:string;


shot:string;


entities:EntityState[];


}


