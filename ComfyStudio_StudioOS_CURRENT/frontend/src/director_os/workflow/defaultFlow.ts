
export const directorWorkflowNodes=[



{

id:"script",

type:"script",

label:"剧本输入节点"

},



{

id:"canon",

type:"canon",

label:"Canon检查节点"

},



{

id:"asset",

type:"asset",

label:"资产一致性节点"

},



{

id:"reference",

type:"reference",

label:"Reference Engine"

},



{

id:"prompt",

type:"prompt",

label:"Prompt编译节点"

},



{

id:"model",

type:"model",

label:"模型路由节点"

},



{

id:"qc",

type:"qc",

label:"质量检查节点"

},



{

id:"delivery",

type:"delivery",

label:"交付归档节点"

}



];




export const directorWorkflowEdges=[



{
source:"script",
target:"canon"
},


{
source:"canon",
target:"asset"
},


{
source:"asset",
target:"reference"
},


{
source:"reference",
target:"prompt"
},


{
source:"prompt",
target:"model"
},


{
source:"model",
target:"qc"
},


{
source:"qc",
target:"delivery"
}


];



