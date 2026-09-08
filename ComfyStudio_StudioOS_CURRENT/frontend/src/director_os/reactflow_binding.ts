

import {
defaultReactFlowNodes
}
from "./default_reactflow_nodes";


import {
defaultReactFlowEdges
}
from "./default_reactflow_edges";


import {
directorReactFlowNodeTypes
}
from "./reactflow_node_types";



export function loadDirectorWorkflow(){


return {


nodes:
defaultReactFlowNodes,


edges:
defaultReactFlowEdges,


nodeTypes:
directorReactFlowNodeTypes



};


}



