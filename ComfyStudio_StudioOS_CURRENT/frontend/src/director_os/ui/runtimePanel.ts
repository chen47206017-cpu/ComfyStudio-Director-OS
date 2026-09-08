

export interface RuntimeLog{


time:string;


node:string;


message:string;


status:string;


}



export const runtimeLogs:RuntimeLog[]=[];



export function addRuntimeLog(
log:RuntimeLog
){


runtimeLogs.push(log);


}



