
export function buildSeedanceRequest(
data:any
){



return {


model:
data.model || "Seedance 2.5",


duration:
data.duration || 6,


referenceImages:
data.references || [],


prompt:
data.prompt,


negative:
"禁止人物漂移，禁止年代错误"



};



}



