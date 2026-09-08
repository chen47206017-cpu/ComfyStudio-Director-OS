
export interface CharacterCanon{

id:string;

name:string;

age:number;

faceDNA?:string;

costume?:string;

}


export interface PropCanon{

id:string;

name:string;

year:number;

status:string;

}



export interface SceneCanon{

id:string;

name:string;

year:number;

location:string;

}



export interface ShotCanon{

episode:string;

shot:string;

year:number;

characters:string[];

props:string[];

scene:string;

}


