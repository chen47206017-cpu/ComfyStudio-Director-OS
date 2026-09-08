

import React from "react";


import {
routeModel
}
from "../model_router/router";



export default function ModelNode({data}:any){



function select(){


const model=
routeModel(data);



console.log(
"Selected Model",
model
);



return model;


}



return (

<div>


<h3>
模型路由节点
</h3>


<button
onClick={select}
>

自动选择模型

</button>


</div>

);


}



