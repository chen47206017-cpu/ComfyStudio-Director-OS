
import {
ReferencePackage
}
from "./schema";



export function createReferencePackage(
data:any
):ReferencePackage{


return {


shotId:data.shotId,


year:data.year,


characterRefs:
data.characters || [],


sceneRefs:
data.scenes || [],


propRefs:
data.props || [],


videoRefs:
data.videoFrames || []


};


}



