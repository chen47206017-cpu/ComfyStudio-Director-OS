

import {

validateCharacterAsset

}

from "../asset_engine/validator";



export class AssetEngine{


validate(

id:string,

year:number,

age:number

){


return validateCharacterAsset(

id,

year,

age

);


}



}



