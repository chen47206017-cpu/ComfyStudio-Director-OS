

import {

createReferencePackage

}

from "../reference_engine/reference_package";



import {

validateReferencePackage

}

from "../reference_engine/validator";





export class ReferenceEngine{



build(data:any){


const pkg=
createReferencePackage(data);



return {


package:pkg,


validation:
validateReferencePackage(pkg)


};



}



}



