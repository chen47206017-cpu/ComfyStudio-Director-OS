@echo off

chcp 65001 >nul

title ComfyStudio Director Factory V4.0


echo ==============================
echo ComfyStudio Director Factory V4.0
echo ==============================


cd /d "F:\一人公司\comfyui-production\ComfyStudio_StudioOS_CURRENT"



if not exist "backend\app.py" (

echo.
echo ERROR:
echo 找不到 backend\app.py
echo.
echo 当前目录:
cd

pause

exit /b

)



echo.
echo Starting Flask...
echo.


python backend\app.py


pause