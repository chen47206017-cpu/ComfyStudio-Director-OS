
export type ReferenceType =

"CHARACTER" |

"SCENE" |

"PROP" |

"LAST_FRAME" |

"VIDEO";


export interface ReferenceAsset{


id:string;


type:ReferenceType;


name:string;


priority:number;


path:string;


locked:boolean;


}



export interface ReferencePack{


character?:ReferenceAsset[];


scene?:ReferenceAsset[];


props?:ReferenceAsset[];


previousFrame?:ReferenceAsset;


video?:ReferenceAsset;


}



