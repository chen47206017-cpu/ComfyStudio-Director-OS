
export class EvidenceRecorder{


records:any[]=[];


record(data:any){


this.records.push(data);


}



list(){

return this.records;


}



}



