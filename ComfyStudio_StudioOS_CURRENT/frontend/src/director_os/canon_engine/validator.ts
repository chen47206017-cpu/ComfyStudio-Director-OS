

import {ShotCanon} from "./schema";


export function validateShot(
shot:ShotCanon
){

const errors:string[]=[];


if(!shot.year){

errors.push(
"YEAR_MISSING"
);

}


if(!shot.characters.length){

errors.push(
"CHARACTER_MISSING"
);

}


return {

pass:
errors.length===0,

errors

};


}


