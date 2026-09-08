
import React,{useState} from "react";

import {

selectDirectorModel

}

from "../model_router/director_router";




export default function ModelRouterNode({data}:any){


const[result,setResult]=useState<any>(null);



function execute(){


const output=
selectDirectorModel({

quality:data.quality || 90,

budget:data.budget || 50,

speed:data.speed || 70,

preferLocal:data.preferLocal || false

});


setResult(output);


}




return (

<div>

<h3>
模型智能路由
</h3>


<button
onClick={execute}
>

自动选择模型

</button>



{

result &&

<div>

模型:

{result.model}

<br/>

评分:

{result.score}

<br/>

原因:

{result.reason}


</div>


}


</div>

);


}



