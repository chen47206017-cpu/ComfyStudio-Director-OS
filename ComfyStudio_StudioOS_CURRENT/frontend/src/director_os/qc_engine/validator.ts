

import {

QCResult

}

from "./schema";




export function inspectShot(
ctx:any
):QCResult{



const errors:string[]=[];


const warnings:string[]=[];



// 年代检查

if(
ctx.characters
){

ctx.characters.forEach(
(c:any)=>{


if(
c.year &&
c.year!==ctx.year
){


errors.push(
"AGE_CONFLICT"
);


}



});


}






// 场景检查


if(
ctx.scene &&
ctx.scene.year!==ctx.year
){


errors.push(
"SCENE_YEAR_CONFLICT"
);


}






// 道具检查


if(ctx.props){


ctx.props.forEach(
(p:any)=>{


if(
p.year &&
p.year!==ctx.year
){


errors.push(
"PROP_YEAR_CONFLICT"
);


}


});


}







// Reference检查


if(
!ctx.references
){


warnings.push(
"REFERENCE_MISSING"
);


}





const score=
Math.max(
0,
100-errors.length*20-warnings.length*5
);





return {


pass:
errors.length===0,


score,


errors,


warnings



};



}



