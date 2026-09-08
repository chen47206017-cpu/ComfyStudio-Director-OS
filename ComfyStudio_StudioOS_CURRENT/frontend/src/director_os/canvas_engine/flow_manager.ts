

export class FlowManager{


nodes:any[]=[];


edges:any[]=[];



addNode(node:any){


this.nodes.push(node);


}



connect(
source:string,
target:string
){


this.edges.push({


source,


target


});


}



getFlow(){


return {


nodes:this.nodes,


edges:this.edges


};


}



}



