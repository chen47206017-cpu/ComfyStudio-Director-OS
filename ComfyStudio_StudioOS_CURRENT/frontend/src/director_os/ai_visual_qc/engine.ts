
export function visualQC(
frame:any
){


const issues:string[]=[];



if(!frame.faceLock){

issues.push(
"FACE_DRIFT"
);

}



if(!frame.timeline){

issues.push(
"TIMELINE_ERROR"
);

}



return {


pass:
issues.length===0,


issues,


score:
100-issues.length*20



};



}



