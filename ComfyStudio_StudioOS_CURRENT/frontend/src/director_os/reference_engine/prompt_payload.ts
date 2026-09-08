

export interface ReferencePayload{


positive:string[];


negative:string[];


}



export function buildReferencePrompt(

refs:any[]

){



const positive:string[]=[];

const negative:string[]=[];



refs.forEach(r=>{


if(r.tags){

positive.push(

...r.tags

);

}



if(r.forbidden){

negative.push(

...r.forbidden

);

}


});



return {

positive,

negative

};



}



