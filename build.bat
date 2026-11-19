@echo off
REM Gera dist\Calcularte.exe (rode em um PC com Windows e Python instalado)
python -m pip install --upgrade pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name Calcularte --paths calcularte calcularte\app.py || exit /b 1
echo.
echo Pronto: dist\Calcularte.exe
