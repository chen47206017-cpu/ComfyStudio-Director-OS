

import {
modelProfiles
}
from "./models";



export function routeModel(
requirement:any
){



if(
requirement.characterConsistency
&&
requirement.multiReference
){

return modelProfiles.SEEDANCE_25;

}



if(
requirement.local
){

return modelProfiles.COMFY_LOCAL;

}



if(
requirement.fast
){

return modelProfiles.SEEDANCE_20;

}



return modelProfiles.WAN30;


}



