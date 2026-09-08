

import {

referenceRegistry

}

from "./registry";



export function buildReferencePack(
shot:any
){



const pack:any={};



if(shot.character){


pack.character=

shot.character.map(
(x:string)=>

(referenceRegistry as any)[x]

);


}



if(shot.scene){


pack.scene=

(referenceRegistry as any)[shot.scene];


}



if(shot.props){


pack.props=

shot.props.map(
(x:string)=>

(referenceRegistry as any)[x]

);


}



if(shot.previousFrame){


pack.previousFrame={

type:"LAST_FRAME",

path:shot.previousFrame

};


}



if(shot.video){


pack.video={

type:"VIDEO",

path:shot.video

};


}



return pack;


}



