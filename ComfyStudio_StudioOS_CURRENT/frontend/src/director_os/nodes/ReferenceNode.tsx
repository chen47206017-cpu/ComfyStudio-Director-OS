import React from "react";

import {

ReferenceEngine

}

from "../engines/reference_engine";



const engine=new ReferenceEngine();



export default function ReferenceNode(
{data}:any
){


function checkReference(){


const result=
engine.validate(
data.referenceId
);



console.log(
"Reference Check",
result
);


return result;


}



return (

<div>

<h3>
参考资产节点
</h3>


<div>
{data.referenceId}
</div>


<button
onClick={checkReference}
>

执行参考一致性检查

</button>


</div>

);


}

