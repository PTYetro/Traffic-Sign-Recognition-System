@echo off
chcp 936 >nul
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "BACKEND_PORT=8001"
set "FRONTEND_PORT=5173"

:CHECK_STATUS
set "BACKEND_RUNNING=0"
set "FRONTEND_RUNNING=0"
set "ELECTRON_RUNNING=0"

set "BACKEND_PID="
set "FRONTEND_PID="
set "ELECTRON_PIDS="

rem ------------------------------
rem 检查后端 8001 端口
rem ------------------------------
call :GET_PORT_PID %BACKEND_PORT% BACKEND_PID
if defined BACKEND_PID set "BACKEND_RUNNING=1"

rem ------------------------------
rem 检查前端 5173 端口
rem ------------------------------
call :GET_PORT_PID %FRONTEND_PORT% FRONTEND_PID
if defined FRONTEND_PID set "FRONTEND_RUNNING=1"

rem ------------------------------
rem 检查 Electron 进程
rem ------------------------------
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq electron.exe" /fo table /nh ^| find /i "electron.exe"') do (
    if defined ELECTRON_PIDS (
        set "ELECTRON_PIDS=!ELECTRON_PIDS!,%%p"
    ) else (
        set "ELECTRON_PIDS=%%p"
    )
)
if defined ELECTRON_PIDS set "ELECTRON_RUNNING=1"

if "%BACKEND_RUNNING%"=="1" goto MENU
if "%FRONTEND_RUNNING%"=="1" goto MENU
if "%ELECTRON_RUNNING%"=="1" goto MENU

goto START_ALL

:MENU
cls
echo ==============================
echo 交通标志识别系统一键启动
echo ==============================
echo.
echo 检测到程序已启动或未正常关闭，请执行以下操作：
echo.

call :SHOW_STATUS

echo.
echo 1. 退出残留进程后重新启动程序
echo 2. 退出启动程序
echo.
set /p CHOICE=请输入操作选项，按回车确认: 

if "%CHOICE%"=="1" goto CLEAN_AND_RESTART
if "%CHOICE%"=="2" goto EXIT_SCRIPT

echo.
echo 输入错误，请重新输入。
timeout /t 2 /nobreak >nul
goto MENU

:CLEAN_AND_RESTART
echo.
echo 正在关闭残留进程...

call :KILL_PORT_PROCESS %BACKEND_PORT%
call :KILL_PORT_PROCESS %FRONTEND_PORT%

if defined ELECTRON_PIDS (
    echo 正在关闭 Electron 进程: %ELECTRON_PIDS%
    taskkill /F /T /IM electron.exe >nul 2>nul
)

timeout /t 2 /nobreak >nul

echo 清理完成，准备重新启动...
goto CHECK_STATUS

:START_ALL
cls
echo ==============================
echo 交通标志识别系统一键启动
echo ==============================
echo.
echo 未检测到运行中的实例，开始启动...
echo.

rem 1. 启动后端
start "交通标志识别系统-后端" cmd /k "cd /d %ROOT% && call .venv\Scripts\activate.bat && uvicorn backend.app:app --host 127.0.0.1 --port %BACKEND_PORT%"

timeout /t 3 /nobreak >nul

rem 2. 启动前端
start "交通标志识别系统-前端" cmd /k "cd /d %ROOT%\frontend && npm run dev"

timeout /t 5 /nobreak >nul

rem 3. 启动 Electron
start "交通标志识别系统-Electron" cmd /k "cd /d %ROOT%\desktop && npm start"

echo.
echo 启动命令已执行完成。
echo 如果某个模块未成功启动，请查看对应终端窗口中的报错信息。
pause
goto END

:EXIT_SCRIPT
echo.
echo 已退出启动程序。
pause
goto END

:SHOW_STATUS
if "%BACKEND_RUNNING%"=="1" (
    echo [残留] 后端服务：PID=%BACKEND_PID% ，端口=%BACKEND_PORT%
) else (
    echo [正常] 后端服务：未检测到残留
)

if "%FRONTEND_RUNNING%"=="1" (
    echo [残留] 前端服务：PID=%FRONTEND_PID% ，端口=%FRONTEND_PORT%
) else (
    echo [正常] 前端服务：未检测到残留
)

if "%ELECTRON_RUNNING%"=="1" (
    echo [残留] Electron：PID=%ELECTRON_PIDS%
) else (
    echo [正常] Electron：未检测到残留
)
exit /b

:GET_PORT_PID
set "%2="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%1 .*LISTENING"') do (
    set "%2=%%p"
    goto :eof
)
exit /b

:KILL_PORT_PROCESS
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%1 .*LISTENING"') do (
    echo 正在关闭占用端口 %1 的进程 PID=%%p
    taskkill /F /T /PID %%p >nul 2>nul
)
exit /b

:END
endlocal
exit /b