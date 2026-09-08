import React from "react";

import {
ReferenceEngine
}
from "../engines/reference_engine";


export default function ReferenceNode({data}:any){


function buildReference(){


const engine =
new ReferenceEngine();



const result =
engine.build(data);



console.log(
"Reference Package",
result
);



return result;


}



return (

<div>

<h3>
Reference Engine
</h3>


<button
onClick={buildReference}
>

生成参考资产包

</button>


</div>

);


}

