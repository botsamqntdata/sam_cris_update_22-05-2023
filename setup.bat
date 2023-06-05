@echo off
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

call env.bat
"C:\Program Files\WinRAR\WinRAR.exe" x -y "%CD%\packages.zip"
SET cmd11=pip install cmake==3.18.2.post1
SET cmd12=pip install "%CD%\packages\dlib-19.21.0-cp36-cp36m-win_amd64.whl"
SET cmd13=pip install "%CD%\packages\simpleaudio-1.0.4-cp36-cp36m-win_amd64.whl"
SET cmd2=pip install -r "%CD%\requirements.txt"
SET cmd3=rd /q/s %CD%\packages
start cmd /k "activate sam_interns & %cmd11% & %cmd12% & %cmd13% & %cmd2% & %cmd3% & pause & exit"
