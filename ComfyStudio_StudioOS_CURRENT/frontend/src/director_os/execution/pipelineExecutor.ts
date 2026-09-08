

import {
executeNode
}
from "./nodeExecutor";



export async function executePipeline(
nodes:any[]
){


const results=[];



for(
const node of nodes
){


const result=
await executeNode(node);



results.push(result);



if(
result.status==="FAILED"
){

break;

}



}



return results;



}



