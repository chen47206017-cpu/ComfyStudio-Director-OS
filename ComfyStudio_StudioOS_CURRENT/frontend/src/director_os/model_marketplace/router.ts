
export function chooseModel(
task:any
){


if(task.faceLock)
return "Seedance 2.5";


if(task.lowCost)
return "ComfyUI";


return "Seedance 2.0";


}



