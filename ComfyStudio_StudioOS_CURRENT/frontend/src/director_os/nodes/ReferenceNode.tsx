
import React from "react";


import {

ReferenceEngine

}

from "../engines/reference_engine";



export default function ReferenceNode(

{data}:any

){



const engine=new ReferenceEngine();



function resolve(){


console.log(

engine.resolve(data.references)

);


}



return (

<div>


<h3>

Reference参考节点

</h3>


<button

onClick={resolve}

>

加载参考资产

</button>


</div>


)


}



