

import {

DirectorAgent

}

from "./director_agent/agent";



import {

ProductionScheduler

}

from "./scheduler/scheduler";




export class DirectorOS{


agent=
new DirectorAgent();



scheduler=
new ProductionScheduler();




run(command:any){



const plan=
this.agent.execute(command);



return {


plan,


scheduler:
this.scheduler.run()



};



}



}



