"""Command line harness for tuning the engine without the UI.

    python -m bilingualz.cli align samples/en.txt samples/pt.txt --show 15
    python -m bilingualz.cli align samples/en.txt samples/pt.txt --json pairs.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, ingest
from .align import align_with_anchors
from .config import LOW_CONFIDENCE


def _read(path: str) -> str:
    return Path(path).expanduser().read_text(encoding="utf-8")


def cmd_align(args: argparse.Namespace) -> int:
    en = ingest.split_paragraphs(_read(args.en))
    pt = ingest.split_paragraphs(_read(args.pt))

    if not en or not pt:
        print("One of the inputs produced no paragraphs.", file=sys.stderr)
        return 1

    forced = []
    for spec in args.anchor or []:
        a, b = spec.split(",")
        forced.append((int(a), int(b)))

    pairs = align_with_anchors(en, pt, forced)

    print(f"en paragraphs : {len(en)}")
    print(f"pt paragraphs : {len(pt)}")
    print(f"pairs         : {len(pairs)}")
    low = sum(1 for p in pairs if p.score < LOW_CONFIDENCE)
    print(f"low confidence: {low}")

    shown = 0
    for index, pair in enumerate(pairs):
        if args.show is not None and shown >= args.show:
            break
        flag = "!" if pair.score < LOW_CONFIDENCE else " "
        en_text = " / ".join(en[i] for i in pair.en)[:64]
        pt_text = " / ".join(pt[j] for j in pair.pt)[:64]
        print(f"{flag} [{index:>4}] {pair.score:.2f}  {en_text}")
        print(f"              {pt_text}")
        shown += 1

    if args.json:
        payload = [pair.to_dict() for pair in pairs]
        Path(args.json).write_text(json.dumps(payload, indent=1), encoding="utf-8")
        print(f"wrote {args.json}")

    return 0


def cmd_split(args: argparse.Namespace) -> int:
    chunks = ingest.split_paragraphs(_read(args.path))
    for index, chunk in enumerate(chunks):
        print(f"[{index:>3}] {chunk[:100]}")
    print(f"\n{len(chunks)} paragraphs")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bilingualz")
    parser.add_argument("--version", action="version", version=f"bilingualz {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    align = sub.add_parser("align", help="align two text files and print the path")
    align.add_argument("en")
    align.add_argument("pt")
    align.add_argument("--show", type=int, default=20)
    align.add_argument("--anchor", action="append", metavar="EN,PT")
    align.add_argument("--json", metavar="PATH")
    align.set_defaults(func=cmd_align)

    split = sub.add_parser("split", help="show how a file gets segmented")
    split.add_argument("path")
    split.set_defaults(func=cmd_split)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
