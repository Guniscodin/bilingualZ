@echo off
REM Build the Windows executable. Run this from the project root on Windows.
setlocal

if not exist ".venv" (
    echo Creating virtual environment...
    py -3.12 -m venv .venv || goto :error
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

REM --- Offline translator (slim) -------------------------------------------
REM Argos without spaCy/stanza/torch. Those are ~1.5 GB and only used by its
REM default sentence splitter; the app pins ARGOS_CHUNK_TYPE=MINISBD instead.
REM Comment these four lines out for a 50-70 MB build with no offline translator.
python -m pip install argostranslate --no-deps || goto :error
python -m pip install "ctranslate2<5,>=4.0" "sentencepiece<0.3,>=0.2.0" "sacremoses<0.2,>=0.0.53" "minisbd>=0.9" packaging || goto :error
python -c "import argostranslate.translate" || goto :error

REM --- App ----------------------------------------------------------------
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
