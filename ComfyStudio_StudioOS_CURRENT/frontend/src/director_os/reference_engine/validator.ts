

import {

referenceAssets

}

from "./database";



export function validateReference(

id:string,

year:number

){



const issues:string[]=[];



const ref:any=

(referenceAssets as any)[id];



if(!ref){


issues.push(

"REFERENCE_NOT_FOUND"

);


return {


pass:false,

issues


};


}



if(ref.year!==year){


issues.push(

"REFERENCE_YEAR_CONFLICT"

);


}



return {


pass:

issues.length===0,


issues


};



}



