
import {
validateContinuity
}
from "../continuity_engine/validator";



export class ContinuityEngine{


check(
before:any,
after:any
){

return validateContinuity(
before,
after
);


}


}



