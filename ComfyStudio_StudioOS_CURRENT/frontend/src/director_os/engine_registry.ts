
import {CanonEngine} from "./canon_engine";
import {SceneEngine} from "./scene_engine";
import {PropEngine} from "./prop_engine";
import {ReferenceEngine} from "./reference_engine";
import {PromptEngine} from "./prompt_engine";
import {ModelRouterEngine} from "./model_router_engine";
import {QCEngine} from "./qc_engine";


export const engineRegistry={


CANON:
new CanonEngine(),


SCENE:
new SceneEngine(),


PROP:
new PropEngine(),


REFERENCE:
new ReferenceEngine(),


PROMPT:
new PromptEngine(),


MODEL:
new ModelRouterEngine(),


QC:
new QCEngine()


};


