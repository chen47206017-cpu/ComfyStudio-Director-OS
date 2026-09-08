

import {

routeModel

}

from "../model_router/router";




export class ModelRouterEngine{



select(task:any){


return routeModel(task);


}



}



