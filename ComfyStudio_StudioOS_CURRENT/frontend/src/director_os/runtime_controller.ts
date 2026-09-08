

export class DirectorRuntime{


async execute(workflow:any){



for(
const node of workflow.nodes
){


node.status="RUNNING";



// TODO connect engines


node.status="SUCCESS";


}



return workflow;


}



}



