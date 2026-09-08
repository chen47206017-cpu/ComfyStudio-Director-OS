
const {
React,
ReactDOM
}=window;


const {

ReactFlow,
Background,
Controls,
useNodesState,
useEdgesState

}=window.ReactFlow;



function App(){


const [nodes,setNodes,onNodesChange]=useNodesState([

{
id:"script",
position:{x:100,y:100},
data:{label:"剧本节点"}
},


{
id:"shot001",
position:{x:400,y:100},
data:{label:"SHOT001\n生成"}
},


{
id:"ref",
position:{x:700,y:100},
data:{label:"上一镜END5参考"}
}


]);



const [edges,setEdges]=useEdgesState([]);



return React.createElement(

"div",

null,


React.createElement(

"div",

{className:"header"},

"ComfyStudio StudioOS V8.4 Director Canvas"

),



React.createElement(

"div",

{className:"main"},


React.createElement(

"div",

{className:"left"},

"资产库",

React.createElement("div",
{className:"card"},
"苏晚晴25岁"
),

React.createElement("div",
{className:"card"},
"2006设计工作室"
),

React.createElement("div",
{className:"card"},
"米黄色座机"
)


),



React.createElement(

"div",

{className:"center"},


React.createElement(

ReactFlow,

{

nodes:nodes,

edges:edges,

onNodesChange:onNodesChange,

fitView:true

},


React.createElement(Background),

React.createElement(Controls)

)

),



React.createElement(

"div",

{className:"right"},

"导演控制台",

React.createElement("p",null,"模型: MiniMax H3"),

React.createElement("p",null,"比例: 9:16"),

React.createElement("p",null,"参考: 上一镜END5")

)


)


)

}


ReactDOM.createRoot(
document.getElementById("root")
)
.render(
React.createElement(App)
)

