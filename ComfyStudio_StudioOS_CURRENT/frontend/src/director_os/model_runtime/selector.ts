
export function runtimeModelSelect(
task:any
){



if(task.faceLock){

return {


model:"Seedance 2.5",

reason:"人物一致性"



};


}



if(task.lowCost){

return {


model:"ComfyUI",

reason:"成本优化"



};


}



return {


model:"Seedance 2.0",

reason:"综合"



};



}



