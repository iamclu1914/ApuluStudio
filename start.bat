@echo off
echo ========================================
echo   Apulu Suite - Docker Startup Script
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check command line argument
if "%1"=="prod" (
    echo Starting in PRODUCTION mode...
    docker-compose -f docker-compose.prod.yml up -d --build
) else (
    echo Starting in DEVELOPMENT mode...
    docker-compose up -d --build
)

echo.
echo ========================================
echo   Services Starting...
echo ========================================
echo.

timeout /t 10 /nobreak >nul

echo Checking service health...
echo.

docker-compose ps

echo.
echo ========================================
echo   Apulu Suite is running!
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/api/docs
echo.
echo   Commands:
echo     docker-compose logs -f    (view logs)
echo     docker-compose down       (stop all)
echo     docker-compose restart    (restart all)
echo.
pause
