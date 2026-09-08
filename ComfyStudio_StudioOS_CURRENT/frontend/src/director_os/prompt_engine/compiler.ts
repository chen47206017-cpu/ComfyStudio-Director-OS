

import {
PromptPackage
}
from "./schema";



export function compilePrompt(
data:PromptPackage
){



return `

${data.style}


Scene:

${data.scene}


Characters:

${data.characters.join(",")}


Props:

${data.props.join(",")}


Canon Rules:

${data.canon}


Reference:

${data.referenceImages.join(",")}


Camera:

${data.camera}


Lighting:

${data.lighting}



Generate cinematic vertical drama shot.


`;

}



