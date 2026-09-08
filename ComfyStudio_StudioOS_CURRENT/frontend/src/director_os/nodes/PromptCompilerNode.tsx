
import React from "react";


import {

PromptEngine

}

from "../engines/prompt_engine";



export default function PromptCompilerNode(

{data}:any

){



const engine=new PromptEngine();



function compile(){


console.log(

engine.compile(data)

);


}



return (

<div>


<h3>

Prompt生成节点

</h3>


<button

onClick={compile}

>

生成影视Prompt

</button>


</div>


)



}



