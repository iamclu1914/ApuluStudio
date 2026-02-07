@echo off
setlocal EnableDelayedExpansion

REM =============================================================================
REM Apulu Suite Quality Team Runner (Windows)
REM =============================================================================
REM Runs all quality checks locally, coordinating the 4 specialist agents:
REM   1. Test Suites Agent (--persona-qa)
REM   2. Code Review Agent (--persona-refactorer)
REM   3. Documentation Agent (--persona-scribe)
REM   4. Security Review Agent (--persona-security)
REM
REM Usage:
REM   scripts\run-quality-team.bat [options]
REM
REM Options:
REM   --quick         Run quick checks only (lint, type check)
REM   --full          Run full quality audit (all checks)
REM   --backend       Run backend checks only
REM   --frontend      Run frontend checks only
REM   --fix           Auto-fix issues where possible
REM   --help          Show this help message
REM =============================================================================

set "PROJECT_ROOT=%~dp0.."
set "REPORTS_DIR=%PROJECT_ROOT%\quality-reports"
set "QUICK_MODE=0"
set "FULL_MODE=0"
set "BACKEND_ONLY=0"
set "FRONTEND_ONLY=0"
set "AUTO_FIX=0"
set "TOTAL_ERRORS=0"
set "TOTAL_WARNINGS=0"
set "PASSED_CHECKS=0"
set "FAILED_CHECKS=0"

REM Parse arguments
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="--quick" set "QUICK_MODE=1"
if /i "%~1"=="--full" set "FULL_MODE=1"
if /i "%~1"=="--backend" set "BACKEND_ONLY=1"
if /i "%~1"=="--frontend" set "FRONTEND_ONLY=1"
if /i "%~1"=="--fix" set "AUTO_FIX=1"
if /i "%~1"=="--help" goto :show_help
shift
goto :parse_args

:show_help
echo.
echo Apulu Suite Quality Team Runner (Windows)
echo.
echo Usage: scripts\run-quality-team.bat [options]
echo.
echo Options:
echo   --quick         Run quick checks only (lint, type check)
echo   --full          Run full quality audit (all checks)
echo   --backend       Run backend checks only
echo   --frontend      Run frontend checks only
echo   --fix           Auto-fix issues where possible
echo   --help          Show this help message
echo.
echo Examples:
echo   scripts\run-quality-team.bat --quick
echo   scripts\run-quality-team.bat --full
echo   scripts\run-quality-team.bat --backend --fix
exit /b 0

:main
REM Default to quick mode
if "%FULL_MODE%"=="0" if "%BACKEND_ONLY%"=="0" if "%FRONTEND_ONLY%"=="0" set "QUICK_MODE=1"

echo.
echo ===============================================================================
echo   APULU SUITE QUALITY TEAM
echo ===============================================================================
echo.
echo Project Root: %PROJECT_ROOT%
echo Reports Dir:  %REPORTS_DIR%
echo.

REM Ensure reports directory exists
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

cd /d "%PROJECT_ROOT%"

REM Run checks
if "%FRONTEND_ONLY%"=="0" call :backend_checks
if "%BACKEND_ONLY%"=="0" call :frontend_checks

REM Summary
call :print_summary
goto :eof

REM =============================================================================
REM Backend Checks
REM =============================================================================
:backend_checks
echo.
echo ===============================================================================
echo   BACKEND QUALITY CHECKS
echo ===============================================================================
echo.

if not exist "backend" (
    echo [ERROR] Backend directory not found
    set /a FAILED_CHECKS+=1
    goto :eof
)

cd /d "%PROJECT_ROOT%\backend"

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Linting
echo.
echo --- Linting (Ruff) ---
echo.

where ruff >nul 2>&1
if %ERRORLEVEL% equ 0 (
    if "%AUTO_FIX%"=="1" (
        ruff check . --fix
        if !ERRORLEVEL! equ 0 (
            echo [PASS] Ruff linting passed (with fixes)
            set /a PASSED_CHECKS+=1
        ) else (
            echo [FAIL] Ruff linting failed
            set /a FAILED_CHECKS+=1
        )
        ruff format .
    ) else (
        ruff check .
        if !ERRORLEVEL! equ 0 (
            echo [PASS] Ruff linting passed
            set /a PASSED_CHECKS+=1
        ) else (
            echo [FAIL] Ruff linting failed
            set /a FAILED_CHECKS+=1
        )
    )
) else (
    echo [WARN] Ruff not installed, skipping
    set /a TOTAL_WARNINGS+=1
)

REM Type checking
echo.
echo --- Type Checking (MyPy) ---
echo.

where mypy >nul 2>&1
if %ERRORLEVEL% equ 0 (
    mypy app --ignore-missing-imports --no-error-summary 2>nul
    if !ERRORLEVEL! equ 0 (
        echo [PASS] MyPy type check passed
        set /a PASSED_CHECKS+=1
    ) else (
        echo [WARN] MyPy found type issues
        set /a TOTAL_WARNINGS+=1
    )
) else (
    echo [WARN] MyPy not installed, skipping
    set /a TOTAL_WARNINGS+=1
)

REM Tests (if not quick mode)
if "%QUICK_MODE%"=="0" (
    echo.
    echo --- Running Tests (pytest) ---
    echo.

    where pytest >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        pytest -v --asyncio-mode=auto --cov=app --cov-report=term-missing
        if !ERRORLEVEL! equ 0 (
            echo [PASS] Backend tests passed
            set /a PASSED_CHECKS+=1
        ) else (
            echo [FAIL] Backend tests failed
            set /a FAILED_CHECKS+=1
        )
    ) else (
        echo [WARN] pytest not installed, skipping
        set /a TOTAL_WARNINGS+=1
    )
)

REM Security scan (if full mode)
if "%FULL_MODE%"=="1" (
    echo.
    echo --- Security Scan (Bandit) ---
    echo.

    where bandit >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        bandit -r app -ll -ii -f txt
        if !ERRORLEVEL! equ 0 (
            echo [PASS] Bandit security scan passed
            set /a PASSED_CHECKS+=1
        ) else (
            echo [WARN] Bandit found security issues
            set /a TOTAL_WARNINGS+=1
        )
    ) else (
        echo [WARN] Bandit not installed, skipping
        set /a TOTAL_WARNINGS+=1
    )
)

cd /d "%PROJECT_ROOT%"
goto :eof

REM =============================================================================
REM Frontend Checks
REM =============================================================================
:frontend_checks
echo.
echo ===============================================================================
echo   FRONTEND QUALITY CHECKS
echo ===============================================================================
echo.

if not exist "frontend" (
    echo [ERROR] Frontend directory not found
    set /a FAILED_CHECKS+=1
    goto :eof
)

cd /d "%PROJECT_ROOT%\frontend"

REM Check for node_modules
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm ci
)

REM Linting
echo.
echo --- Linting (ESLint) ---
echo.

call npm run lint
if %ERRORLEVEL% equ 0 (
    echo [PASS] ESLint passed
    set /a PASSED_CHECKS+=1
) else (
    echo [FAIL] ESLint found issues
    set /a FAILED_CHECKS+=1
)

REM Type checking
echo.
echo --- Type Checking (TypeScript) ---
echo.

call npx tsc --noEmit
if %ERRORLEVEL% equ 0 (
    echo [PASS] TypeScript check passed
    set /a PASSED_CHECKS+=1
) else (
    echo [FAIL] TypeScript errors found
    set /a FAILED_CHECKS+=1
)

REM Build test (if not quick mode)
if "%QUICK_MODE%"=="0" (
    echo.
    echo --- Build Test ---
    echo.

    set "NEXT_PUBLIC_API_URL=http://localhost:8000/api"
    call npm run build
    if !ERRORLEVEL! equ 0 (
        echo [PASS] Production build succeeded
        set /a PASSED_CHECKS+=1
    ) else (
        echo [FAIL] Build failed
        set /a FAILED_CHECKS+=1
    )
)

REM Security audit (if full mode)
if "%FULL_MODE%"=="1" (
    echo.
    echo --- Security Audit (npm audit) ---
    echo.

    call npm audit --audit-level=high
    if !ERRORLEVEL! equ 0 (
        echo [PASS] npm audit passed
        set /a PASSED_CHECKS+=1
    ) else (
        echo [WARN] npm audit found vulnerabilities
        set /a TOTAL_WARNINGS+=1
    )
)

cd /d "%PROJECT_ROOT%"
goto :eof

REM =============================================================================
REM Summary
REM =============================================================================
:print_summary
echo.
echo ===============================================================================
echo   QUALITY TEAM SUMMARY
echo ===============================================================================
echo.
echo Checks Passed:  %PASSED_CHECKS%
echo Checks Failed:  %FAILED_CHECKS%
echo Total Errors:   %TOTAL_ERRORS%
echo Total Warnings: %TOTAL_WARNINGS%
echo.

if %FAILED_CHECKS% equ 0 (
    echo ========================================
    echo      QUALITY GATE: PASSED
    echo ========================================
    exit /b 0
) else (
    echo ========================================
    echo      QUALITY GATE: FAILED
    echo ========================================
    echo.
    echo Run with --fix to auto-fix issues where possible.
    exit /b 1
)
