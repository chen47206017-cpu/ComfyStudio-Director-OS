
export function analyzeEpisode(
episode:any
){


const risk=[];


if(!episode.hook){

risk.push(
"HOOK_MISSING"
)

}



return {


hookScore:
risk.length?70:95,


conflictScore:90,


emotionScore:90,


risk,


suggestions:[

"增强前三秒冲突",

"提高信息密度"

]


};


}


