
export interface DeliveryAsset{


id:string;


episode:string;


shot:string;


type:string;


file:string;


model:string;


version:string;


status:string;


createdAt:string;


}



export interface DeliveryReport{


success:boolean;


assets:number;


issues:string[];


}


