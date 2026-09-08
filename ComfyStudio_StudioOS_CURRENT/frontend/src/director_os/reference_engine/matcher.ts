

export function matchReference(

assets:any[],

type:string

){


return assets.filter(

asset=>

asset.type===type

);


}



