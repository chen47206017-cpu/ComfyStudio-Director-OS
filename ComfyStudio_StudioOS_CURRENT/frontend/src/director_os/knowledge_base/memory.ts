

const memoryStore:any={};



export function saveMemory(
key:string,
value:any
){


memoryStore[key]=value;


}



export function readMemory(
key:string
){


return memoryStore[key];


}



export function exportProjectMemory(){


return memoryStore;


}



