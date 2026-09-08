
export class ComfyProvider{


name="ComfyUI";


async generate(task:any){


return {


provider:this.name,


status:"SUBMITTED"


};


}


}


