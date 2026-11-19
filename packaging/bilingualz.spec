# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for the Windows build.

Run from the project root:

    pyinstaller packaging/bilingualz.spec --noconfirm

Produces dist/Bilingualz/Bilingualz.exe (one folder, fast startup).

If ``argostranslate`` is importable at build time it is bundled too, which makes
offline translation work inside the frozen app. Install it first:

    pip install -e ".[translate]"
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = Path(SPECPATH).resolve()
PROJECT = SPEC_DIR.parent

hidden = collect_submodules("bilingualz")
hidden += collect_submodules("webview")

datas = [(str(PROJECT / "bilingualz" / "web"), "bilingualz/web")]

# Optional: offline translation engine.
try:
    import argostranslate  # noqa: F401
    import ctranslate2  # noqa: F401

    hidden += collect_submodules("argostranslate")
    hidden += collect_submodules("ctranslate2")
    hidden += ["sentencepiece", "stanza", "sacremoses"]
except ImportError:
    pass

a = Analysis(
    [str(PROJECT / "run.py")],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "test",
        "tests",
        "pytest",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Bilingualz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed app: no black terminal window
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Bilingualz",
)
