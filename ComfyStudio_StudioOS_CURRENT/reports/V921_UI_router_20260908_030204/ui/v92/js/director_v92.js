
async function load(){


let agent=

await fetch(
"/api/v8/swarm/status"
);


document
.getElementById("agents")
.innerHTML=

await agent.text();



let memory=

await fetch(
"/api/v8/memory/search"
);


document
.getElementById("memory")
.innerHTML=

await memory.text();



let pipe=

await fetch(
"/api/v8/pipeline/status"
);


document
.getElementById("pipeline")
.innerHTML=

await pipe.text();



}


load();


