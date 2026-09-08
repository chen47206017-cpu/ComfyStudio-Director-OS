
export class TaskMonitor{


tasks:any[]=[];


update(task:any){


this.tasks.push(task);


}



list(){

return this.tasks;


}


}


