
export class ErrorCollector{


errors:any[]=[];


add(error:any){


this.errors.push(error);


}


report(){

return this.errors;

}


}



