

import {

saveWorkflow

}

from "./workflow_storage";



export function persistReactFlow(
nodes:any[],
edges:any[]
){



return saveWorkflow({


id:"CURRENT",


name:"当前导演工程",


version:"1.0",


createdAt:
new Date().toISOString(),


updatedAt:
new Date().toISOString(),


nodes,


edges,


metadata:{


project:"Director OS",


status:"EDITING"



}



});



}



