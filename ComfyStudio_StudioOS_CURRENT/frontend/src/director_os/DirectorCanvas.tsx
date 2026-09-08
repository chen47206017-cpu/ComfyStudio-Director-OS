import React from "react";

import ReactFlow,{
Background,
Controls
} from "reactflow";


import "reactflow/dist/style.css";


import {directorNodeTypes}
from "./directorNodeTypes";


const nodes=[


{
id:"script",
type:"script",
position:{x:0,y:0},
data:{
label:"剧本节点"
}
},


{
id:"canon",
type:"canon",
position:{x:250,y:0},
data:{
label:"Canon检查"
}
},


{
id:"asset",
type:"asset",
position:{x:500,y:0},
data:{
label:"资产一致性"
}
},


{
id:"prompt",
type:"prompt",
position:{x:750,y:0},
data:{
label:"Prompt Compiler"
}
}


]



const edges=[


{
id:"e1",
source:"script",
target:"canon"
},


{
id:"e2",
source:"canon",
target:"asset"
},


{
id:"e3",
source:"asset",
target:"prompt"
}


]


export default function DirectorCanvas(){


return (

<div style={{
height:"100%"
}}>


<ReactFlow

nodes={nodes}

edges={edges}

nodeTypes={directorNodeTypes}

fitView

>


<Background/>

<Controls/>


</ReactFlow>


</div>

)

}

