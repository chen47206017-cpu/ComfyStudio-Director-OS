

export interface SavedWorkflow{


id:string;


name:string;


nodes:any[];


edges:any[];


updatedAt:string;


}



export function saveWorkflow(
workflow:SavedWorkflow
){


return {


...workflow,


updatedAt:
new Date().toISOString()


};


}



