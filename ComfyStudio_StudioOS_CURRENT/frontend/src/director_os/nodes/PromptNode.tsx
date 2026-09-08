import React,{useState} from "react";


import {
compilePrompt
}
from "../prompt_engine/compiler";



export default function PromptNode({data}:any){


const [result,setResult]=useState<any>(null);



function execute(){


const output=
compilePrompt(
data.shot || {}
);



setResult(output);


console.log(
"PROMPT COMPILE RESULT",
output
);


}



return (

<div
style={{
padding:"12px",
border:"1px solid #666",
borderRadius:"8px"
}}
>


<h3>
Prompt编译节点
</h3>


<p>
自动生成Seedance/ComfyUI提示词
</p>


<button
onClick={execute}
>

生成生产提示词

</button>



{
result &&

<div>

<h4>
Seedance Prompt
</h4>

<textarea
value={result.seedance}
readOnly
rows={8}
/>



<h4>
ComfyUI Prompt
</h4>

<textarea
value={result.comfyui}
readOnly
rows={8}
/>


</div>

}



</div>

)

}

