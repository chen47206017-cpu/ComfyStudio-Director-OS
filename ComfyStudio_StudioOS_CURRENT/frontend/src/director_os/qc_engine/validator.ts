

import {

qcRules

}

from "./rules";



export function runQC(
ctx:any
){



const issues:string[]=[];




// 年代检查

const forbidden:any=

(qcRules.timeline as any)[ctx.year];



if(forbidden){


for(
const item of forbidden
){


if(
JSON.stringify(ctx.props)
.includes(item)

){


issues.push(
"TIMELINE_PROP_CONFLICT:"+item
);


}


}



}





// 场景检查


if(
ctx.scene.includes("2006")
&&
ctx.prompt.includes("未来")

){


issues.push(
"SCENE_TIME_MIX"
);


}







// 时空融合检查


if(
ctx.prompt.includes("三层")

){


issues.push(
"TIME_SPACE_MERGE"
);


}






return {


passed:
issues.length===0,


level:

issues.length===0

?"PASS"

:"BLOCK",



issues



};



}



