
import {

validateReference

}

from "../reference_engine/validator";




export class ReferenceEngine{


validate(id:string){


return validateReference(
id
);


}



}



