

export function detectVisualError(
frame:any
){


const issues:string[]=[];



if(
!frame.reference
){


issues.push(
"REFERENCE_MISSING"
);


}



if(
frame.ageMismatch
){


issues.push(
"AGE_DRIFT"
);


}



if(
frame.propError
){


issues.push(
"PROP_ERROR"
);


}




return {


pass:
issues.length===0,


score:
100-
issues.length*20,


issues



};



}



