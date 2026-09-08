
export interface CanonResult{

pass:boolean;

issues:string[];

}



export function createCanonResult(
pass:boolean,
issues:string[]
):CanonResult{


return {

pass,

issues

};

}


