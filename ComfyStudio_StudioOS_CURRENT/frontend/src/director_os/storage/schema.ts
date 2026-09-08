
export interface SavedWorkflow{


id:string;


name:string;


version:string;


createdAt:string;


updatedAt:string;


nodes:any[];


edges:any[];


metadata:{


project:string;


episode?:string;


status:string;


};



}



