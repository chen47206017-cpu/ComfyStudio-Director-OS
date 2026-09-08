

import {

validateReference

}

from "../reference_engine/validator";



export class ReferenceEngine{


check(

id:string,

year:number

){


return validateReference(

id,

year

);


}



}



