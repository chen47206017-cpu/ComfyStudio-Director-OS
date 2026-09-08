

export function buildSeedancePrompt(
compiled:any
){



return {


prompt:

compiled.positive,


negative:

compiled.negative,


reference:

compiled.references



};



}



