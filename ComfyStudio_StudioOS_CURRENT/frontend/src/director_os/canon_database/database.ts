

const database:any[]=[];



export function saveCanon(
record:any
){


database.push(record);


}



export function queryCanon(
id:string
){


return database.filter(
x=>x.id===id
);


}



export function getAllCanon(){


return database;


}



