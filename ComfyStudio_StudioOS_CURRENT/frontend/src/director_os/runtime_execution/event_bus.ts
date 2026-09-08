
export class EventBus{


events:any[]=[];


emit(
event:string,
data:any
){


this.events.push({

event,

data,

time:new Date()

});


}


list(){

return this.events;


}


}


