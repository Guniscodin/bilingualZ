@echo off
REM Build the Windows executable. Run this from the project root on Windows.
setlocal

if not exist ".venv" (
    echo Creating virtual environment...
    py -3.12 -m venv .venv || goto :error
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

REM Base app. Add ".[translate]" instead if you want Argos bundled inside.
python -m pip install -e ".[dev]" || goto :error

python -m pytest -q || goto :error

pyinstaller packaging\bilingualz.spec --noconfirm || goto :error

echo.
echo Built: dist\Bilingualz\Bilingualz.exe
echo Optional installer: install Inno Setup, then run:
echo     iscc packaging\bilingualz.iss
exit /b 0

:error
echo Build failed.
exit /b 1
