@echo off
openfiles >nul 2>nul
if %errorlevel% NEQ 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c %~s0' -Verb runAs"
    exit /b
)

py -m pip install psutil pyinstaller pywin32
py SMS.py install
py SMS.py start
