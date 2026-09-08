
const versions:any={};



export function saveVersion(
shot:string,
data:any
){


if(!versions[shot])
versions[shot]=[];


versions[shot].push(data);



}



export function bestVersion(
shot:string
){


return versions[shot]
?.sort(
(a:any,b:any)=>
b.qcScore-a.qcScore
)[0];

}



