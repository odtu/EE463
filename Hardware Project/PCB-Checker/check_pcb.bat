@echo off
rem EE463 PCB checker for Windows.
rem Drag a .kicad_pcb file, a project folder or your submission .zip onto this file,
rem or run:  check_pcb.bat MyBoard.kicad_pcb
setlocal
set "PY="
for %%V in (10.0 9.0 8.0) do (
  if not defined PY if exist "%ProgramFiles%\KiCad\%%V\bin\python.exe" set "PY=%ProgramFiles%\KiCad\%%V\bin\python.exe"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Could not find KiCad 8/9/10 or Python. Install KiCad from https://www.kicad.org and try again.
  pause
  exit /b 2
)
if "%~1"=="" (
  echo Drag your .kicad_pcb file, project folder or submission .zip onto check_pcb.bat
  pause
  exit /b 2
)
"%PY%" "%~dp0check_pcb.py" %* --open
echo.
pause
