import React from "react";


export default function DeliveryNode(props:any){

return (

<div className="director-node">

<strong>
{props.data?.label || "DeliveryNode"}
</strong>


<div>

状态:
{props.data?.status || "等待"}

</div>


</div>

)

}

