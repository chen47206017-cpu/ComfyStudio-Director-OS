
import {sceneAssets}

from "./scenes";


export function validateScene(

id:string,

year:number

){


const issues:string[]=[];


const scene:any=(sceneAssets as any)[id];


if(!scene){

issues.push("SCENE_NOT_FOUND");

return {

pass:false,

issues

};

}


if(scene.year!==year){

issues.push("YEAR_CONFLICT");

}


return {


pass:issues.length===0,

issues


};


}


