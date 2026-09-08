

import {
DirectorPlanner
}
from "./planner";



export class DirectorRuntime{


planner=
new DirectorPlanner();



execute(
command:any
){


return this.planner.plan(
command
);


}



}



