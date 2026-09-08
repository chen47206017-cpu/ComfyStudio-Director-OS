

import {

qcRules

}

from "./rules";



export function runQC(

context:any

){



const issues:string[]=[];



// 年代检查


if(

context.year===2006

&&

context.prompt.includes("智能手机")

){

issues.push(

"YEAR_DEVICE_CONFLICT"

);

}




// Prompt完整性


for(

const field of qcRules.requiredPromptFields

){


if(

!context.prompt.includes(field)

){

issues.push(

"PROMPT_FIELD_MISSING_"+field

);


}


}




return {


pass:

issues.length===0,


level:

issues.length===0

?

"PASS"

:

"FAILED",


issues


};



}



