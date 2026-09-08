
export function runRealityCheck(){


return [


{

module:
"Canon",

status:
"CHECK_REQUIRED",

message:
"等待真实Canon执行"



},


{

module:
"Prompt",

status:
"CHECK_REQUIRED",

message:
"等待真实Prompt生成"



},


{

module:
"ComfyUI",

status:
"CHECK_REQUIRED",

message:
"等待真实API连接"



},


{

module:
"Video",

status:
"CHECK_REQUIRED",

message:
"等待真实视频输出"



}


];


}



