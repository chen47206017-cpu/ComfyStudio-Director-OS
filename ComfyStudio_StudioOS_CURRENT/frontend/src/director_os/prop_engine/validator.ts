
import {
propAssets
}
from "./props";


import {
propContinuity
}
from "./continuity";



export function validateProp(

id:string,

year:number

){


const issues:string[]=[];


const prop:any=
(propAssets as any)[id];



if(!prop){

issues.push(
"PROP_NOT_FOUND"
);


return {

pass:false,

issues

};

}



if(prop.year!==year){

issues.push(
"YEAR_CONFLICT"
);

}



const rule:any=
(propContinuity as any)[id];


if(
rule &&
!rule.allowedYears.includes(year)
){

issues.push(
"PROP_TIME_LOCK_FAILED"
);

}



return {


pass:
issues.length===0,


issues


};



}


