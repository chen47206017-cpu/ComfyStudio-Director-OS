
import {
engineRegistry
}
from "./engine_registry";



export class DirectorRuntime{


async execute(workflow:any){


for(
const node of workflow.nodes
){


node.status="RUNNING";


try{


const engine:any=
(engineRegistry as any)[node.type];



if(engine){


const result=
await engine.check?
engine.check(node.data)
:
engine.run?
engine.run(node.data)
:
engine.select?
engine.select(node.data)
:
engine.build?
engine.build(node.data)
:
null;



node.data.result=result;



}



node.status="SUCCESS";


}
catch(error){


node.status="FAILED";


node.data.error=
String(error);


}



}


return workflow;


}



}


