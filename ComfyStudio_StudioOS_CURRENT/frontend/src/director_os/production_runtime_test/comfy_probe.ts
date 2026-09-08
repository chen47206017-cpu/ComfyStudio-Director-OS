
export async function checkComfyUI(){


try{


const response=
await fetch(
"http://127.0.0.1:8188/system_stats"
);



return {


connected:true,


data:
await response.json()



};


}

catch(e){


return {


connected:false,


error:
String(e)


};



}


}



