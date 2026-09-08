

const registry:any={};



export function registerAsset(
asset:any
){


registry[asset.id]=asset;


}



export function getAsset(
id:string
){


return registry[id];


}



