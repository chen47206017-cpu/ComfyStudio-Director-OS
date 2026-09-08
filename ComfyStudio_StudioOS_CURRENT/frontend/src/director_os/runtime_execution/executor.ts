
export class Executor{


runner=
new NodeRunner();



async execute(flow:any){


const result=[];


for(const node of flow.nodes){


result.push(
await this.runner.run(node,{})
);


}


return result;


}



}


