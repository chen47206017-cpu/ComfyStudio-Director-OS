

export interface PromptRuntime{


status:

"EMPTY"

|

"COMPILING"

|

"READY"

|

"FAILED";



seedance?:string;


comfyui?:string;



}



export const defaultPromptRuntime={


status:"EMPTY"


};



