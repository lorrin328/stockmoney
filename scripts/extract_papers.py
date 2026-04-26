#!/usr/bin/env python3
"""提取 papers/ 中所有 PDF 的文本到 txt 文件，便于阅读和引用."""
import pdfplumber, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PAPERS = ROOT / "papers"
OUT = ROOT / "papers" / "_text"
OUT.mkdir(exist_ok=True)

pdfs = sorted(PAPERS.glob("*.pdf"))
if not pdfs:
    print("No PDFs found in", PAPERS)
    sys.exit(1)

for pdf_path in pdfs:
    out_path = OUT / f"{pdf_path.stem}.txt"
    if out_path.exists():
        print(f"SKIP (exists): {pdf_path.name}")
        continue
    full_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text.append(f"--- Page {i} ---\n{text}")
    except Exception as e:
        print(f"ERROR {pdf_path.name}: {e}")
        continue
    out_path.write_text("\n\n".join(full_text), encoding="utf-8")
    print(f"EXTRACTED: {pdf_path.name} -> {out_path.name} ({len(full_text)} pages)")

print("Done.")
