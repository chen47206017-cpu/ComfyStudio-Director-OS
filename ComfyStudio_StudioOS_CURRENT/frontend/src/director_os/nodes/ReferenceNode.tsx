import React from "react";


export default function ReferenceNode(props:any){

return (

<div className="director-node">

<strong>
{props.data?.label || "ReferenceNode"}
</strong>


<div>

状态:
{props.data?.status || "等待"}

</div>


</div>

)

}

