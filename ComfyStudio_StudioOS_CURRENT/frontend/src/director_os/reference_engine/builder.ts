

import {
referenceAssets
}
from "./assets";



export function buildReferencePack(
shot:any
){



const assets=[];



if(shot.character){

assets.push(
(referenceAssets as any)[shot.character]
);

}



if(shot.scene){

assets.push(
(referenceAssets as any)[shot.scene]
);

}



if(shot.props){

shot.props.forEach(
(p:string)=>{

assets.push(
(referenceAssets as any)[p]
);

}

)

}



return {


shotId:shot.id,


assets,


inheritPrevious:
true



};



}



