
export function buildStudioPrompt(
data:any
){


return {


story:data.story,


visual:data.visual,


camera:data.camera,


audio:data.audio,


negative:


"禁止年龄漂移，禁止时代错误，道具错误",


model:data.model



};


}



