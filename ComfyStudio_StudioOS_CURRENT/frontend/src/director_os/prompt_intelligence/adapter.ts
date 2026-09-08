

export function convertPrompt(
prompt:string,
model:string
){



return {


model,


positive:


prompt,


negative:


"禁止身份漂移，禁止年代错误"



};



}



