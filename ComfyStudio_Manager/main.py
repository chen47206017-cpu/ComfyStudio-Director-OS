import tkinter as tk
from tkinter import messagebox

from core.detector import check


def run_check():

    data=check()


    text=""

    for k,v in data.items():

        text+=f"{k}: {v}\n\n"


    messagebox.showinfo(
        "ComfyStudio检查结果",
        text
    )



app=tk.Tk()

app.title(
"ComfyStudio Production Manager"
)

app.geometry(
"500x400"
)


label=tk.Label(
app,
text="""
ComfyStudio Production Manager

Production Core 1.0
""",
font=("Microsoft YaHei",16)
)


label.pack(
pady=30
)



btn=tk.Button(
app,
text="开始环境检测",
command=run_check,
width=25,
height=2
)


btn.pack()



app.mainloop()

