

export type RuntimeEvent=


"NODE_START"


|


"NODE_SUCCESS"


|


"NODE_FAILED";




export interface RuntimeMessage{


type:RuntimeEvent;


nodeId:string;


time:string;


}




export function createRuntimeEvent(
type:RuntimeEvent,
nodeId:string
){


return {


type,


nodeId,


time:
new Date().toISOString()



};


}



