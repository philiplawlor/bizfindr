@echo off
setlocal enabledelayedexpansion

echo Setting up BizFindr development environment...

:: Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not installed. Please install Docker and try again.
    exit /b 1
)

:: Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker Compose is not installed. Please install Docker Compose and try again.
    exit /b 1
)

:: Create .env file from example if it doesn't exist
if not exist "..\backend\.env" (
    echo Creating .env file from .env.example...
    copy "..\backend\.env.example" "..\backend\.env" >nul
    
    :: Generate a random API key if not set
    findstr /i /c:"API_KEY=" "..\backend\.env" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Generating API key...
        echo. >> "..\backend\.env"
        echo # API Key for authentication >> "..\backend\.env"
        for /f "delims=" %%a in ('powershell -Command "[guid]::NewGuid().ToString()"') do set API_KEY=%%a
        echo API_KEY=!API_KEY! >> "..\backend\.env"
    )
) else (
    echo .env file already exists. Skipping creation.
)

:: Build and start the application
echo Building and starting the application...
cd ..
docker-compose build --no-cache
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to build Docker containers.
    exit /b 1
)

docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to start services with Docker Compose.
    exit /b 1
)

:: Initialize the database
echo Initializing the database...
docker-compose exec backend python scripts/init_db.py

if %ERRORLEVEL% neq 0 (
    echo Warning: Failed to initialize the database. The application might not work correctly.
)

echo.
echo Setup complete!
echo - Web interface: http://localhost:5000
echo - API: http://localhost:5000/api
echo - MongoDB: mongodb://localhost:27017/bizfindr
echo.
echo To stop the application, run: .\scripts\stop.bat
echo To view logs, run: docker-compose logs -f

endlocal
