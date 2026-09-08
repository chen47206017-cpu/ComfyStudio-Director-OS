
import React from "react";

import {
 validateShot
} from "../canon_engine/validator";


export default function CanonNode({data}:any){


function runCheck(){


const result=validateShot(
data.shot
);


console.log(
"Canon Result",
result
);


return result;

}


return (

<div>

<h3>
Canon检查节点
</h3>


<button
onClick={runCheck}
>

执行Canon检查

</button>


</div>

);


}

