
const {

app,

BrowserWindow

}=require("electron");


const path=require("path");



function createWindow(){



const win=new BrowserWindow({


width:1600,


height:1000,


title:

"ComfyStudio Director OS"


});



win.loadURL(

"http://localhost:5173"

);



}



app.whenReady()

.then(createWindow);



