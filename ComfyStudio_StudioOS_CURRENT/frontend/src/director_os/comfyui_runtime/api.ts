
export class ComfyAPI{


constructor(
private host=
"http://127.0.0.1:8188"
){}



async submit(
workflow:any
){


const result={


promptId:
"PROMPT_"+Date.now(),


status:
"QUEUED"



};


return result;


}



async status(
id:string
){


return {


id,


status:
"RUNNING"



};



}



}



