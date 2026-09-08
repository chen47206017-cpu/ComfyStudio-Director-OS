

export function validateReferencePackage(

pkg:any

){


const issues:string[]=[];



if(!pkg.shotId)

issues.push(
"SHOT_ID_MISSING"
);



if(
pkg.characterRefs.length===0
)

issues.push(
"CHARACTER_REFERENCE_MISSING"
);



if(
pkg.sceneRefs.length===0
)

issues.push(
"SCENE_REFERENCE_MISSING"
);



return {


pass:
issues.length===0,


issues


};


}



