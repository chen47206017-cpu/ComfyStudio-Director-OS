

import {SceneEngine}
from "../engines/scene_engine";


import {PropEngine}
from "../engines/prop_engine";


import {DeliveryEngine}
from "../engines/delivery_engine";




export const engineRegistry={


scene:
new SceneEngine(),


prop:
new PropEngine(),


delivery:
new DeliveryEngine()



};



