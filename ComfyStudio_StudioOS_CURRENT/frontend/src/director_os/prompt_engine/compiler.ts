

import {
PromptContext,
CompiledPrompt
}
from "./schema";



export function compilePrompt(
ctx:PromptContext
):CompiledPrompt{



let positive=`

${ctx.year}年代真人影视画面，

角色:
${ctx.character.join(",")}

场景:
${ctx.scene}

道具:
${ctx.props.join(",")}

情绪:
${ctx.emotion}

镜头:
${ctx.camera}

时长:
${ctx.duration}秒

`;




let negative=`

禁止年龄漂移，

禁止人物身份变化，

禁止现代物品进入旧年代，

禁止错误电话设备，

禁止空间穿越，

禁止多人融合。



`;



return {


positive,


negative,


references:
ctx.referencePack



};



}



