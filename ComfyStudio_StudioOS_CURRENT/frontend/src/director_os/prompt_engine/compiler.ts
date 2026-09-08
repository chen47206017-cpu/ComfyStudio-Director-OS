

import {

CompiledPrompt

}

from "./schema";




export function compilePrompt(

shot:any

):CompiledPrompt{


const constraints=[



`年份限制:${shot.year}`,


`场景:${shot.scene}`,


`角色:${shot.characters?.join(",")}`,


`道具:${shot.props?.join(",")}`,


`参考:${shot.references?.join(",")}`



];





const seedance=`


影视级真人短剧镜头。


年份:
${shot.year}


场景:
${shot.scene}


角色:
${shot.characters?.join(",")}


动作:
${shot.action}


镜头:
${shot.camera}


光影:
${shot.lighting}


对白:
${shot.dialogue}



严格保持人物身份、年代、场景、道具一致。


`;





const comfyui=`

positive:

${seedance}



negative:

wrong age,

wrong year,

modern props,

character change,

scene mismatch



`;




return {


seedance,


comfyui,


constraints


};



}



