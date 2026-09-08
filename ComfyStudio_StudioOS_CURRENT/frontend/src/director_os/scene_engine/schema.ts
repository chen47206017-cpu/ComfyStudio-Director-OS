
export interface SceneAsset{

id:string;

name:string;

year:number;

location:string;

style:string;

lighting:string;

fixedProps:string[];

forbidden:string[];

referenceImages:string[];

}


export interface SceneValidation{

pass:boolean;

issues:string[];

}

