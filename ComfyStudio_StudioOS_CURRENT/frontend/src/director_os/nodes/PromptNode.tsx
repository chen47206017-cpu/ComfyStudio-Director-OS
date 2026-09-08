

import React from "react";


import {

compilePrompt

}

from "../prompt_engine/compiler";





export default function PromptNode(
{data}:any
){



function compile(){


const result=
compilePrompt(
data.shot
);



console.log(
"Compiled Prompt",
result
);



}



return (

<div>


<h3>
提示词编译节点
</h3>


<button
onClick={compile}
>

生成生产Prompt

</button>



</div>


);



}


