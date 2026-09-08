

export function estimateCost(
model:string,
seconds:number
){


const prices:any={


Seedance2.5:1,


Seedance2.0:0.7,


ComfyUI:0.3



};



return {


model,


seconds,


estimatedCost:

seconds*
(prices[model]||1)



};



}



