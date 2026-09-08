

import React from "react";


import {
DeliveryEngine
}
from "../engines/delivery_engine";



export default function DeliveryNode({data}:any){


const engine=
new DeliveryEngine();



function save(){


const result=
engine.save(data);



console.log(
"Delivery",
result
);



}



return (

<div>


<h3>
交付归档节点
</h3>


<button
onClick={save}
>

保存版本

</button>


</div>

);


}



