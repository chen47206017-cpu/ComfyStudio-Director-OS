
export class ProductionQueue{


tasks:any[]=[];



push(task:any){


this.tasks.push(task);


}



run(){


return this.tasks.map(t=>{


t.status="RUNNING";


return t;


});


}



}



