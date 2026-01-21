@echo off
REM HippoCLI Docker Wrapper Script for Windows
REM Simplifies running HippoCLI commands with Docker Compose

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Check if docker-compose is available
where docker-compose >nul 2>&1
if errorlevel 1 (
    where docker >nul 2>&1
    if errorlevel 1 (
        echo Error: Docker is not installed or not in PATH
        exit /b 1
    )
    set "DOCKER_COMPOSE_CMD=docker compose"
) else (
    set "DOCKER_COMPOSE_CMD=docker-compose"
)

REM Build if needed (only on first run or if image doesn't exist)
docker images | findstr /C:"hippocli" | findstr /C:"hippocli" >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    %DOCKER_COMPOSE_CMD% build --quiet
)

REM Run the command
%DOCKER_COMPOSE_CMD% run --rm hippocli %*
