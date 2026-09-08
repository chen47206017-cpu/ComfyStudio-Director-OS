
export function validateSceneMemory(
previous:any,
current:any
){


const issues:string[]=[];


if(
previous.layout!==current.layout
){

issues.push(
"SCENE_LAYOUT_CHANGED"
);

}


return {


pass:
issues.length===0,


issues



};


}



