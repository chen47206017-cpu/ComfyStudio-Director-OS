

const projects:any[]=[];



export function createProject(
project:any
){


projects.push(project);


}



export function listProjects(){


return projects;


}



export function archiveProject(
id:string
){



const item=
projects.find(
p=>p.id===id
);



if(item){

item.status="ARCHIVED";


}



}



