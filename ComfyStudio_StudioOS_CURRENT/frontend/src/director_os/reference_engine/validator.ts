

export function validateReferencePack(
pack:any
){



const issues=[];



if(
!pack.assets ||
pack.assets.length===0
){

issues.push(
"NO_REFERENCE"
);


}



return {


pass:
issues.length===0,


issues



};



}



