

import {
SavedWorkflow
}
from "./schema";



const STORAGE_KEY=
"COMFY_STUDIO_DIRECTOR_WORKFLOW";



export function saveWorkflow(
workflow:SavedWorkflow
){


localStorage.setItem(

STORAGE_KEY,

JSON.stringify(workflow)

);


return {


success:true,

time:new Date().toISOString()

};


}





export function loadWorkflow(){


const data=
localStorage.getItem(
STORAGE_KEY
);



if(!data){

return null;

}



return JSON.parse(data);



}





export function clearWorkflow(){


localStorage.removeItem(
STORAGE_KEY
);


}



