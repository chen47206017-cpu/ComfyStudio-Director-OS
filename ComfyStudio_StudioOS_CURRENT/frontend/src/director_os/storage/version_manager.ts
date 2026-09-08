

export function createWorkflowVersion(
workflow:any
){


return {


id:
"WF-"+Date.now(),


version:
"1.0.0",


createdAt:
new Date().toISOString(),


updatedAt:
new Date().toISOString(),


nodes:
workflow.nodes,


edges:
workflow.edges,


metadata:{


project:"ComfyStudio Director OS",


status:"DRAFT"



}



};


}



