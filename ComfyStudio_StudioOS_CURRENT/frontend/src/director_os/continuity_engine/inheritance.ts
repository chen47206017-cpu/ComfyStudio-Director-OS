
export function compareShotState(
previous:any,
current:any
){


const issues:string[]=[];



for(
const p of previous.entities
){


const found=
current.entities.find(
(e:any)=>e.id===p.id
);



if(
p.status!==undefined
&&
!found
){

issues.push(

"ENTITY_LOST:"+p.id

);

}


}



return {

pass:
issues.length===0,

issues

};


}


