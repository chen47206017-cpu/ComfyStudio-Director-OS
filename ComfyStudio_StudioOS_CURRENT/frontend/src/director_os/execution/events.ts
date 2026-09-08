

export interface ExecutionEvent{


nodeId:string;


event:

"START"

|

"SUCCESS"

|

"FAILED";



timestamp:string;



}



export function createEvent(
nodeId:string,
event:any
){


return {


nodeId,


event,


timestamp:
new Date().toISOString()



};


}



