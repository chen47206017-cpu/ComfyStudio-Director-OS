
import {
referenceAssets
}
from "./assets";



export function validateReference(
id:string
){


const issues:string[]=[];


const asset:any=
(referenceAssets as any)[id];



if(!asset){

issues.push(
"REFERENCE_NOT_FOUND"
);


return {

pass:false,

issues

};

}



if(!asset.locked){

issues.push(
"REFERENCE_UNLOCKED"
);

}



return {


pass:
issues.length===0,


issues


};


}



