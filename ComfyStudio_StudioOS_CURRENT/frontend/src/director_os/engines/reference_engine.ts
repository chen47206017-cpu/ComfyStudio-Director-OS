

import {

resolveReference

}

from "../reference_engine/resolver";




export class ReferenceEngine{


buildShotReference(

shot:any

){


return {


shotId:shot.id,


assets:

resolveReference(

shot

)


};


}


}



