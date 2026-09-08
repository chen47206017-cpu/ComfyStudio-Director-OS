

import React from "react";


import {

ReferenceEngine

}

from "../engines/reference_engine";




export default function ReferenceNode(

{data}:any

){



const engine=new ReferenceEngine();



function generate(){

const result=

engine.buildShotReference(

data.shot

);



console.log(

"Reference Result",

result

);


}



return (

<div>

<h3>

参考图绑定节点

</h3>


<button

onClick={generate}

>

生成参考资产包

</button>


</div>

)



}



