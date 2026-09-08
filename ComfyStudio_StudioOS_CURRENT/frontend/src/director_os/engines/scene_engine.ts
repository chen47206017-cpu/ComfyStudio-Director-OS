
import {

validateScene

}

from "../scene_engine/validator";


export class SceneEngine{


validate(id:string,year:number){


return validateScene(

id,

year

);


}


}

