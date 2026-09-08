
export function checkOwnership(
entity:any
){


const issues:string[]=[];



if(!entity.owner){

issues.push(
"OWNER_MISSING"
);

}


return {

pass:
issues.length===0,

issues

};


}


