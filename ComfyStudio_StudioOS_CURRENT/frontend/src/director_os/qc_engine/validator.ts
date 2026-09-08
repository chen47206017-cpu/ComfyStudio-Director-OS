

import {
qcRules
}
from "./rules";



export function runQC(
data:any
){



const issues:string[]=[];



if(!data.canon){

issues.push(
"CANON_MISSING"
);

}



if(!data.reference){

issues.push(
"REFERENCE_MISSING"
);

}



if(!data.prompt){

issues.push(
"PROMPT_MISSING"
);

}



return {


pass:
issues.length===0,


score:
100-(issues.length*15),


issues


};



}



