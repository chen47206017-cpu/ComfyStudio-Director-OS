
export class SQLiteRuntime{


private storage:any[]=[];



insert(data:any){


this.storage.push(data);


}



query(){


return this.storage;


}



}


