

import {

referenceAssets

}

from "./database";




export function resolveReference(

shot:any

){



const result:any[]=[];



if(shot.characters){

shot.characters.forEach(

(c:string)=>{


const asset=

(referenceAssets as any)[c];


if(asset){

result.push(asset);

}


}

)

}



if(shot.scene){

const asset=

(referenceAssets as any)[shot.scene];


if(asset){

result.push(asset);

}

}




if(shot.props){

shot.props.forEach(

(p:string)=>{


const asset=

(referenceAssets as any)[p];


if(asset){

result.push(asset);

}


}

)

}




return result;


}



