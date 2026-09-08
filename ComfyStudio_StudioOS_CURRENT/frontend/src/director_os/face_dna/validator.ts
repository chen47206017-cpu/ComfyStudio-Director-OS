

export function validateFaceDNA(
source:any,
target:any
){


const issues:string[]=[];



if(
source.character!==target.character
){

issues.push(
"IDENTITY_DRIFT"
);


}



if(
source.age!==target.age
){

issues.push(
"AGE_DRIFT"
);


}



return {


pass:
issues.length===0,


issues



};


}


