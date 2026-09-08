

export interface CanvasNode{


id:string;


type:string;


label:string;


position:{
x:number;
y:number;
};



status:
"等待"
|
"执行中"
|
"完成"
|
"失败";



data:any;



}




export interface CanvasEdge{


source:string;


target:string;



}



