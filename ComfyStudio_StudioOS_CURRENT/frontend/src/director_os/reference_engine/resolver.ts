
import {

references

}

from "./database";



export function resolveReference(

ids:string[]

){



return ids.map(

id=>

(references as any)[id]

)

.filter(Boolean);



}



