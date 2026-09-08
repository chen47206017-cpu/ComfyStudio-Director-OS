
export class CacheManager{


cache:any={};



set(key:string,value:any){


this.cache[key]=value;


}



get(key:string){


return this.cache[key];


}



}



