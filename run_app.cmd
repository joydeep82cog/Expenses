@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"
set "MAIN_PY=%PROJECT_DIR%main.py"

if not exist "%PYTHON_EXE%" (
  echo ERROR: Missing virtual environment interpreter:
  echo   %PYTHON_EXE%
  echo.
  echo Create it with Python 3.12 and reinstall requirements.
  pause
  exit /b 1
)

if not exist "%MAIN_PY%" (
  echo ERROR: Could not find:
  echo   %MAIN_PY%
  pause
  exit /b 1
)

if "%KIVY_GL_BACKEND%"=="" set "KIVY_GL_BACKEND=angle_sdl2"

"%PYTHON_EXE%" "%MAIN_PY%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Application exited with code %EXIT_CODE%.
  pause
)

exit /b %EXIT_CODE%
