import React from "react";


export default function CanonNode(props:any){

return (

<div className="director-node">

<strong>
{props.data?.label || "CanonNode"}
</strong>


<div>

状态:
{props.data?.status || "等待"}

</div>


</div>

)

}

