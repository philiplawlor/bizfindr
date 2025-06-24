@echo off
setlocal enabledelayedexpansion

echo Stopping BizFindr application...

:: Stop and remove containers, networks, and volumes
cd ..
docker-compose -f docker-compose.yml down -v

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to stop services with Docker Compose.
    exit /b 1
)

echo.
echo BizFindr has been stopped.
echo To start the application again, run: .\scripts\start.bat

endlocal
