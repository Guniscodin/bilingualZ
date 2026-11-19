# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for the Windows build.

Run from the project root:

    pyinstaller packaging/bilingualz.spec --noconfirm

Produces dist/Bilingualz/Bilingualz.exe (one folder, fast startup).

Offline translation
-------------------
If ``argostranslate`` is importable at build time it is bundled, which makes
translate mode work with no network and no API key. We bundle only its light
runtime: CTranslate2 + sentencepiece + MiniSBD. spaCy, stanza and torch are
deliberately excluded (and excluded again below), because Argos only needs them
for its default sentence splitter - MiniSBD replaces them for ~80 MB instead of
~1.5 GB. ``bilingualz/translate/argos.py`` pins ARGOS_CHUNK_TYPE=MINISBD.

Install the slim set first:

    pip install argostranslate --no-deps
    pip install "ctranslate2<5,>=4.0" "sentencepiece<0.3,>=0.2.0" \
                "sacremoses<0.2,>=0.0.53" minisbd packaging
    pip install -e ".[dev]"
"""

import importlib
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

SPEC_DIR = Path(SPECPATH).resolve()
PROJECT = SPEC_DIR.parent

hidden = collect_submodules("bilingualz")
hidden += collect_submodules("webview")

datas = [(str(PROJECT / "bilingualz" / "web"), "bilingualz/web")]
binaries = []

# Native/data-carrying packages that need more than a plain import to survive
# freezing. Each is optional so a base build still works without them.
HEAVY = [
    "argostranslate",
    "ctranslate2",
    "minisbd",
    "sentencepiece",
    "sacremoses",
    "onnxruntime",
]

for name in HEAVY:
    try:
        importlib.import_module(name)
    except Exception:
        continue
    try:
        extra_datas, extra_binaries, extra_hidden = collect_all(name)
    except Exception:
        continue
    datas += extra_datas
    binaries += extra_binaries
    hidden += extra_hidden

a = Analysis(
    [str(PROJECT / "run.py")],
    pathex=[str(PROJECT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # GUI toolkits pywebview does not use on Windows
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        # Argos optional sentence splitters we intentionally do not ship
        "spacy",
        "thinc",
        "blis",
        "cymem",
        "preshed",
        "murmurhash",
        "srsly",
        "stanza",
        "torch",
        # dev-only
        "test",
        "tests",
        "pytest",
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
