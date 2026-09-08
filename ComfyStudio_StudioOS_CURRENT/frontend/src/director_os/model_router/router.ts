

import {

modelRegistry

}

from "./models";




export function routeModel(
task:any
){



if(
task.priority==="QUALITY"
){


return modelRegistry.SEEDANCE_25;


}



if(
task.priority==="SPEED"
){


return modelRegistry.SEEDANCE_FAST;


}



if(
task.local===true
){


return modelRegistry.COMFY_LOCAL;


}




return modelRegistry.SEEDANCE_25;



}



