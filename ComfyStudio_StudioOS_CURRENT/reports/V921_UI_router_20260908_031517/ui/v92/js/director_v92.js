
async function load(){


let status=

await fetch(
"/api/v8/ui/status"
);


document
.getElementById("status")
.innerHTML=

await status.text();



let memory=

await fetch(
"/api/v8/memory/search"
);


document
.getElementById("memory")
.innerHTML=

await memory.text();



let pipeline=

await fetch(
"/api/v8/pipeline/status"
);


document
.getElementById("pipeline")
.innerHTML=

await pipeline.text();


}


load();


