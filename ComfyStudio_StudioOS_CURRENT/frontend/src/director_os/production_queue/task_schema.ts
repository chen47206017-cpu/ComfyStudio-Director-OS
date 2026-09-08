
export interface ProductionTask{


id:string;


episode:string;


shot:string;


type:
"IMAGE"
|
"VIDEO"
|
"QC";



priority:number;



status:
"WAITING"
|
"RUNNING"
|
"DONE"
|
"FAILED";



payload:any;



}


