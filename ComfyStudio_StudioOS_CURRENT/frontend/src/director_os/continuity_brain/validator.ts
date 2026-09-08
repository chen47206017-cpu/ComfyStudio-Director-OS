

export function checkContinuity(
previous:any,
current:any
){


const issues:string[]=[];


const warnings:string[]=[];



if(
previous.year &&
current.year &&
previous.year!==current.year
){


warnings.push(
"YEAR_CHANGE"
);


}



if(
previous.character &&
current.character &&
previous.character!==current.character
){


issues.push(
"CHARACTER_DRIFT"
);


}




return {


pass:
issues.length===0,


issues,


warnings



};



}



