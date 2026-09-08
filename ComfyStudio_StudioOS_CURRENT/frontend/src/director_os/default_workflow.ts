
import {
DirectorWorkflow
}
from "./workflow_schema";



export const defaultDirectorWorkflow:DirectorWorkflow={


id:"NEW_PROJECT",


name:"导演生产流程",



nodes:[


{
id:"script",
type:"SCRIPT",
status:"WAITING",
data:{}
},


{
id:"canon",
type:"CANON",
status:"WAITING",
data:{}
},


{
id:"character",
type:"CHARACTER",
status:"WAITING",
data:{}
},


{
id:"scene",
type:"SCENE",
status:"WAITING",
data:{}
},


{
id:"prop",
type:"PROP",
status:"WAITING",
data:{}
},


{
id:"reference",
type:"REFERENCE",
status:"WAITING",
data:{}
},


{
id:"prompt",
type:"PROMPT",
status:"WAITING",
data:{}
},


{
id:"model",
type:"MODEL",
status:"WAITING",
data:{}
},


{
id:"qc",
type:"QC",
status:"WAITING",
data:{}
},


{
id:"delivery",
type:"DELIVERY",
status:"WAITING",
data:{}
}


],




edges:[


["script","canon"],

["canon","character"],

["character","scene"],

["scene","prop"],

["prop","reference"],

["reference","prompt"],

["prompt","model"],

["model","qc"],

["qc","delivery"]


]


};


