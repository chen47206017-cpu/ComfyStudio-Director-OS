
import {
NodeExecutionResult
}
from "./types";



export async function executeNode(
node:any
):Promise<NodeExecutionResult>{



console.log(
"START NODE",
node.id
);



return {


nodeId:node.id,


status:"SUCCESS",


message:
`${node.id} executed`



};



}



