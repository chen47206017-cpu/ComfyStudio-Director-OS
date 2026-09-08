

import React from "react";


import {
QCEngine
}
from "../engines/qc_engine";



export default function QCNode({data}:any){


const engine=new QCEngine();



function check(){


const result=
engine.check(data);



console.log(
"QC Result",
result
);



}



return (

<div>


<h3>
质量检查节点
</h3>


<button
onClick={check}
>

执行QC检查

</button>


</div>

);


}



