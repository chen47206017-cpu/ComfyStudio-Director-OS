
const queue:any[]=[];


export function addJob(job:any){

queue.push(job);

}


export function nextJob(){

return queue.shift();

}


export function status(){

return queue.length;


}


