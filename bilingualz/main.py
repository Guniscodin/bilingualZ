"""Desktop entry point: one native window, WebView2 on Windows."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .api import Api


def web_root() -> Path:
    """Where index.html lives, both from source and from a frozen bundle."""
    frozen = getattr(sys, "_MEIPASS", None)
    if frozen:
        return Path(frozen) / "bilingualz" / "web"
    return Path(__file__).resolve().parent / "web"


def main() -> int:
    try:
        import webview
    except ImportError:
        print(
            "pywebview is not installed.\n"
            "  pip install -e .\n"
            "or, for a development install without the UI dependencies:\n"
            "  python -m bilingualz.cli align en.txt pt.txt",
            file=sys.stderr,
        )
        return 2

    api = Api()
    window = webview.create_window(
        "Bilingualz",
        str(web_root() / "index.html"),
        js_api=api,
        width=1440,
        height=920,
        min_size=(980, 640),
        background_color="#0b0e13",
        text_select=True,
    )
    api.set_window(window)

    webview.start(debug=bool(os.environ.get("BILINGUALZ_DEBUG")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
