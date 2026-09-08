
export class Logger{


logs:string[]=[];


write(message:string){


this.logs.push(

`${new Date().toISOString()} ${message}`

);


}



read(){


return this.logs;


}



}



