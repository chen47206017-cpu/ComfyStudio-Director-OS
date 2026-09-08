

import {

modelRegistry

}

from "./models";


import {

routerRules

}

from "./rules";





export function smartRoute(
requirement:any
){



let candidates:any[]=[];



Object.values(modelRegistry)
.forEach((m:any)=>{


let score=0;



//质量权重

score +=
m.quality *
(requirement.quality/100);



//成本权重

score +=
(100-m.cost) *
(requirement.budget/100);



//速度权重

score +=
m.speed *
(requirement.speed/100);



//本地优先

if(
requirement.preferLocal &&
m.local
){

score+=20;

}



candidates.push({

model:m.id,

score

});


});



candidates.sort(

(a,b)=>

b.score-a.score

);



return {


model:
candidates[0].model,


score:
candidates[0].score,


reason:
"自动根据质量/成本/速度/本地策略选择"


};


}



