

export function generateShots(
episode:any
){



return {


episode:


episode.id,


shots:[


{


id:
episode.id+"_001",


scene:
"待生成",


year:
2006,


characters:[],


props:[],


emotion:
"未知",


camera:
"默认镜头",


duration:
6



}


]


};



}



