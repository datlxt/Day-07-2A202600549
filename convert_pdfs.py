"""One-off helper: convert the group's PDFs in datanhom/ to markdown in data/."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pymupdf4llm

SRC_DIR = Path("datanhom")
OUT_DIR = Path("data")


def slugify(name: str) -> str:
    """Vietnamese title -> ascii snake_case filename stem."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_only = ascii_only.replace("Đ", "D").replace("đ", "d")
    ascii_only = ascii_only.lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "_", ascii_only).strip("_")
    return ascii_only or "doc"


def clean(text: str, title: str) -> str:
    """Remove per-page watermark noise and collapse blank runs."""
    # Drop "Revision Duku1 N" watermark lines (any casing / spacing).
    text = re.sub(r"(?im)^\s*revision\s+duku1\s+\d+\s*$", "", text)
    # Collapse 3+ blank lines into one blank line.
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()
    return f"# {title}\n\n{text}\n"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for pdf in sorted(SRC_DIR.glob("*.pdf")):
        md_text = pymupdf4llm.to_markdown(str(pdf))
        md_text = clean(md_text, pdf.stem)
        out_path = OUT_DIR / f"{slugify(pdf.stem)}.md"
        out_path.write_text(md_text, encoding="utf-8")
        print(f"OK -> {out_path}  ({len(md_text)} chars)")


if __name__ == "__main__":
    main()
