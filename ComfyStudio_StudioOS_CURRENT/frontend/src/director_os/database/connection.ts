
export class Database{


projects:any[]=[];


save(project:any){


this.projects.push(project);


}


list(){

return this.projects;


}



}



