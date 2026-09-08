

import React from "react";

import {

PromptCompilerEngine

}

from "../engines/prompt_compiler_engine";




export default function PromptNode(

{data}:any

){


const engine=

new PromptCompilerEngine();



function compile(){


const result=

engine.compile(

data.shot

);


console.log(

"Prompt Result",

result

);



}



return (

<div>


<h3>

Prompt编译节点

</h3>


<button

onClick={compile}

>

生成AI提示词

</button>



</div>

)


}



