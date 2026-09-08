

import {

referenceRegistry

}

from "./registry";




export function buildReferencePack(
request:any
){



const pack:any={};



if(request.character){


pack.character=
request.character.map(
(id:string)=>
(referenceRegistry as any)[id]

);


}



if(request.scene){


pack.scene=
request.scene.map(
(id:string)=>
(referenceRegistry as any)[id]

);


}



if(request.props){


pack.props=
request.props.map(
(id:string)=>
(referenceRegistry as any)[id]

);


}



return pack;



}



