

export function resolveConflict(

refs:any[]

){


return refs.sort(

(a,b)=>

b.priority-a.priority

);


}



