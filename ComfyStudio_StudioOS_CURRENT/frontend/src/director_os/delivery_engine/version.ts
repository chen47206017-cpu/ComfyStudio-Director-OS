

export function createVersion(
episode:string,
shot:string
){


return {


id:
`${episode}_${shot}_${Date.now()}`,


version:
"v1",


status:
"CREATED"


};



}



