

const queue:any[]=[];



export function addTask(
task:any
){


queue.push(task);


}



export function getQueue(){


return queue;


}



export function nextTask(){


return queue.shift();


}



