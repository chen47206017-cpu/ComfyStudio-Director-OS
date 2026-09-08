
export interface ProductionResult{


stage:string;

status:string;

message:string;


}


export function checkResult(){

return [

{

stage:"CANON",

status:"WAITING",

message:"等待真实执行"

},


{

stage:"COMFYUI",

status:"WAITING",

message:"等待API响应"

},


{

stage:"VIDEO",

status:"WAITING",

message:"等待MP4输出"

}



];


}


