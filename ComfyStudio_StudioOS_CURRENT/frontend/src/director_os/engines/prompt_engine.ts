

import {
compilePrompt
}
from "../prompt_engine/compiler";



import {
buildSeedancePrompt
}
from "../prompt_engine/seedance";



export class PromptEngine{


run(context:any){


const compiled=
compilePrompt(context);



return buildSeedancePrompt(
compiled
);



}



}



