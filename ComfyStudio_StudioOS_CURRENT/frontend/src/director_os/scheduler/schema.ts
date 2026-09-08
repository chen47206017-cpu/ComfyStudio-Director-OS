

export interface ProductionTask{


id:string;


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



