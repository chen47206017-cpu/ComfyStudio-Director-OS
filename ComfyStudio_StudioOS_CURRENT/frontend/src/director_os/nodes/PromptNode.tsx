

import React from "react";

import {
compilePrompt
}
from "../prompt_engine/compiler";



export default function PromptNode({data}:any){



function generate(){


const prompt=
compilePrompt(data);


console.log(
"Generated Prompt",
prompt
);


return prompt;


}



return (

<div>

<h3>
Prompt编译节点
</h3>


<button
onClick={generate}
>

生成影视提示词

</button>


</div>

);


}


