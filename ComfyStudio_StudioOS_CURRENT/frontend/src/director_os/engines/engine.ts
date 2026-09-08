
/*
 Director OS Engine Layer

V10.4+

Canon Engine
Asset Engine
Reference Engine
Prompt Engine
QC Engine

*/

export interface DirectorEngine{

    name:string;

    execute(data:any):Promise<any>;

}


