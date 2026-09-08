
export function checkTimeline(
year:number,
props:string[]
){


const issues:string[]=[];


if(
year===2006 &&
props.includes("智能手机")
){


issues.push(
"YEAR_PROP_ERROR"
);


}



return {


pass:
issues.length===0,


issues



};


}



