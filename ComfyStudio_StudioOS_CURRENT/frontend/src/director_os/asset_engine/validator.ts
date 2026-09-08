

import {
characterAssets
}
from "./characters";



export function validateCharacterAsset(


id:string,


year:number,


age:number


){



const issues:string[]=[];



const asset:any=
(characterAssets as any)[id];



if(!asset){

issues.push(
"CHARACTER_NOT_FOUND"
);


return {

pass:false,

issues

};

}



if(asset.year!==year){


issues.push(

"YEAR_CONFLICT"

);


}



if(asset.age!==age){


issues.push(

"AGE_CONFLICT"

);


}



return {


pass:

issues.length===0,


issues


};



}



