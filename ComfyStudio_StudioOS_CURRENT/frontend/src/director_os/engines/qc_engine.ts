

import {
runQC
}
from "../qc_engine/validator";



export class QCEngine{


check(
data:any
){


return runQC(data);


}



}



