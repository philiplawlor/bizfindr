@echo off
setlocal enabledelayedexpansion

echo Starting BizFindr application...

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running. Please start Docker and try again.
    exit /b 1
)

:: Create .env file if it doesn't exist
if not exist "..\backend\.env" (
    echo Creating .env file from .env.example...
    copy "..\backend\.env.example" "..\backend\.env" >nul
)

:: Start the application using Docker Compose
echo Starting services with Docker Compose...
cd ..
docker-compose -f docker-compose.yml up -d --build

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to start services with Docker Compose.
    exit /b 1
)

echo.
echo BizFindr is now running!
echo - Web interface: http://localhost:5000
echo - API: http://localhost:5000/api
echo - MongoDB: mongodb://localhost:27017/bizfindr
echo.
echo To stop the application, run: .\scripts\stop.bat
echo To view logs, run: docker-compose logs -f

endlocal
