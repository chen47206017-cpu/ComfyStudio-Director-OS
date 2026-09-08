

import {
EngineDispatcher
}
from "./engine_dispatcher";



export class DirectorRuntime{


dispatcher:
EngineDispatcher;



constructor(){


this.dispatcher=
new EngineDispatcher();


}





async executeNode(
node:any
){



node.status="RUNNING";



try{


const result=
await this.dispatcher.execute(node);



node.status="SUCCESS";



return {


node,


result



};



}
catch(error){


node.status="FAILED";


return {


node,


error



};



}



}





async executeWorkflow(
workflow:any
){



for(
const node of workflow.nodes
){


await this.executeNode(node);


}



return workflow;



}



}



