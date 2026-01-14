@echo on
setlocal


cd /d %~dp0


if not exist "manage.py" (
  echo [ERROR] No se encuentra manage.py en %cd%
  pause
  exit /b 1
)


set PYVENV="%~dp0venv\Scripts\python.exe"
if not exist %PYVENV% (
  echo [ERROR] No se encontro %PYVENV%
  echo Creá/instalá el venv:
  echo   python -m venv venv
  echo   venv\Scripts\activate
  echo   pip install -r requirements.txt
  pause
  exit /b 1
)


set PORT=8000


start "" http://127.0.0.1:%PORT%/


%PYVENV% manage.py runserver %PORT%


echo Codigo de salida: %errorlevel%
pause
endlocal