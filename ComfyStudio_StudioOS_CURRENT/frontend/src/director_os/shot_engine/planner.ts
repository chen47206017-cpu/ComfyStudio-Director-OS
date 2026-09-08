

export function planShot(context:any){


return {


id:
context.id,


shotType:
"medium",


camera:
"cinematic composition",


movement:
"slow push",


emotion:
context.emotion || "neutral",


duration:
6


};


}



