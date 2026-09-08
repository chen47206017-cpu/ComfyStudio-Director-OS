

import {
defaultDirectorFlow
}
from "./workflow";



export async function executeDirectorFlow(data:any){



const result={



workflow:
defaultDirectorFlow,


input:data,


status:
"READY"


};



return result;



}



