

import React from "react";


import {

ReferenceEngine

}

from "../engines/reference_engine";



export default function ReferenceNode(

{data}:any

){


const engine=

new ReferenceEngine();



function check(){


console.log(

engine.check(

data.reference,

data.year

)

);


}



return (

<div>


<h3>

Reference参考引擎节点

</h3>


<button

onClick={check}

>

检查参考资产

</button>


</div>

)



}



