
import {
modelRegistry
}
from "./models";


export function selectModel(requirement:any){


const models=
Object.values(modelRegistry);



return models.sort(
(a:any,b:any)=>
b.quality-a.quality
)[0];


}



