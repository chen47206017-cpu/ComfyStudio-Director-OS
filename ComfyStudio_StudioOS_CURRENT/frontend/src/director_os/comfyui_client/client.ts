
export class ComfyClient{


constructor(
private host=
"http://127.0.0.1:8188"
){}



async submit(workflow:any){


const response=
await fetch(
this.host+"/prompt",
{


method:"POST",


headers:{


"Content-Type":
"application/json"


},


body:
JSON.stringify(
{
prompt:workflow
}
)


}
);



return response.json();


}



}



