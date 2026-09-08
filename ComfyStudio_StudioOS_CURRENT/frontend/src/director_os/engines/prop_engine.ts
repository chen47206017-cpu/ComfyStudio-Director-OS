
import {

validateProp

}

from "../prop_engine/validator";



export class PropEngine{


validate(

id:string,

year:number

){


return validateProp(

id,

year

);


}


}


