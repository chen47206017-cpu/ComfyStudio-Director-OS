
export type ExecutionStatus =

"WAITING" |

"RUNNING" |

"SUCCESS" |

"WARNING" |

"FAILED";



export interface NodeExecutionResult{


nodeId:string;


status:ExecutionStatus;


message:string;


data?:any;



}


