
export type DirectorNodeType=

"SCRIPT" |

"CANON" |

"CHARACTER" |

"SCENE" |

"PROP" |

"REFERENCE" |

"PROMPT" |

"MODEL" |

"QC" |

"DELIVERY";



export interface DirectorNode{


id:string;


type:DirectorNodeType;


status:
"WAITING"
|
"RUNNING"
|
"SUCCESS"
|
"FAILED";


data:any;


}



export interface DirectorWorkflow{


id:string;


name:string;


nodes:DirectorNode[];


edges:any[];


}


