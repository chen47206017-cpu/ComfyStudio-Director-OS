

import {

compilePrompt

}

from "../prompt_engine/compiler";



export class PromptCompilerEngine{


compile(

context:any

){


return compilePrompt(

context

);


}



}



