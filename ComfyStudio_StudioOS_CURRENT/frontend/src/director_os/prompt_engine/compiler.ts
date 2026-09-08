
import {

PromptContext,

CompiledPrompt

}

from "./schema";


import {

promptTemplate

}

from "./templates";



export function compilePrompt(

ctx:PromptContext

):CompiledPrompt{



return {



positive:



`

${promptTemplate.cinematic}


角色:

${ctx.character.join(",")}


场景:

${ctx.scene.join(",")}


道具:

${ctx.props.join(",")}


参考:

${ctx.references.join(",")}



模型:

${ctx.model}


`,



negative:


promptTemplate.forbidden,



qc:[

"人物年龄检查",

"服装检查",

"年代检查",

"道具检查",

"空间检查"

]



};



}



