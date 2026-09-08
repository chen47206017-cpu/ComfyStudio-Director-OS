

import {
SceneEngine
}
from "./engines/scene_engine";


import {
PropEngine
}
from "./engines/prop_engine";


import {
PromptEngine
}
from "./engines/prompt_engine";




export class EngineDispatcher{



async execute(
node:any
){



switch(node.type){



case "SCENE":


return {


success:true,


message:"Scene Engine executed"



};





case "PROP":


return {


success:true,


message:"Prop Engine executed"



};






case "PROMPT":


return {


success:true,


message:"Prompt Compiler executed"



};





case "CANON":


return {


success:true,


message:"Canon Engine executed"



};






default:


return {


success:true,


message:
"Node executed"



};



}



}



}



