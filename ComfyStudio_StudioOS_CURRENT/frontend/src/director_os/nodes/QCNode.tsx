import React from "react";


export default function QCNode(props:any){

return (

<div className="director-node">

<strong>
{props.data?.label || "QCNode"}
</strong>


<div>

状态:
{props.data?.status || "等待"}

</div>


</div>

)

}

