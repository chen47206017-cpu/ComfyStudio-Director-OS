

const taskQueue:any[]=[];



export function pushTask(
task:any
){


taskQueue.push(task);


}



export function getTasks(){


return taskQueue;


}



export function clearTask(
){


taskQueue.length=0;


}



