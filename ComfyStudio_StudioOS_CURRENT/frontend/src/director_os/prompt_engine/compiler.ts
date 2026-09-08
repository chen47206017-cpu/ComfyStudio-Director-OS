

import {

promptTemplates

}

from "./templates";



export function compilePrompt(

context:any

){



let positive=

promptTemplates.cinematic

.replace(

"{{duration}}",

context.duration || 6

)

.replace(

"{{year}}",

context.year

);



let negative=

promptTemplates.negative;



return {


positive,


negative,


model:

context.model ||

"Seedance 2.5"



};



}



