

export class QueueWorker{


async execute(
task:any
){



return {


taskId:
task.id,


status:
"DONE",


message:
"Task finished"



};



}



}


