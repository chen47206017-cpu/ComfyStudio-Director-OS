

export function routeModel(task:any){



if(task.priority==="QUALITY"){


return {


model:"SEEDANCE_25",


reason:"最高人物一致性与影视质量"


};


}



if(task.local===true){


return {


model:"COMFY_LOCAL",


reason:"本地GPU生成"


};


}



if(task.cost==="LOW"){


return {


model:"MINIMAX_H3",


reason:"低成本测试"


};


}



return {


model:"SEEDANCE_20",


reason:"平衡质量成本"


};



}



