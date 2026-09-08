
import CanonNode from "../nodes/CanonNode";
import PromptNode from "../nodes/PromptNode";
import ReferenceNode from "../nodes/ReferenceNode";


export const directorNodeRegistry={


CanonNode:{

id:"CanonNode",

label:"Canon检查节点",

category:"审核",

component:CanonNode

},


ReferenceNode:{

id:"ReferenceNode",

label:"参考资产节点",

category:"资产",

component:ReferenceNode

},


PromptNode:{

id:"PromptNode",

label:"提示词编译节点",

category:"生成",

component:PromptNode

}


};



