

import {

analyzeScript

}

from "./script_analyzer";



import {

generateShots

}

from "./shot_generator";




export class AutoDirector{


createProject(input:any){


return analyzeScript(input);


}




createShots(
episode:any
){


return generateShots(
episode
);


}



}



