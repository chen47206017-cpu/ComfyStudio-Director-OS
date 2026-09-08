

import {
buildReferencePack
}
from "../reference_engine/builder";


import {
validateReferencePack
}
from "../reference_engine/validator";



export class ReferenceEngine{



run(
shot:any
){


const pack=
buildReferencePack(
shot
);



const check=
validateReferencePack(
pack
);



return {


pack,


check



};



}



}



