
export type TaskStatus =

"WAITING"

|

"QUEUED"

|

"RUNNING"

|

"QC"

|

"SUCCESS"

|

"FAILED";



export interface ProductionTask{


id:string;

name:string;

status:TaskStatus;


progress:number;


}


