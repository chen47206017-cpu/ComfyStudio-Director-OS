
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



const execute=()=>{


const result=

engine.resolve(

data.refs

);



console.log(

"Reference Loaded",

result

);


};



return (

<div>


<h3>

参考资产节点

</h3>


<button

onClick={execute}

>

加载角色/场景/道具参考

</button>


</div>

)



}



