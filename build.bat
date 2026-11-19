@echo off
REM Gera dist\Calcularte.exe (rode em um PC com Windows e Python instalado)
python -m pip install -r requirements.txt || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name Calcularte --paths calcularte --collect-all sv_ttk calcularte\app.py || exit /b 1
echo.
echo Pronto: dist\Calcularte.exe
