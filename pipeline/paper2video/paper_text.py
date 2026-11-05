#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paper_text.py — 论文 PDF → 纯文本（喂给 PROMPT-EXTRACT 的输入）
用法：
  python paper_text.py paper.pdf paper.txt                 # 全文
  python paper_text.py paper.pdf paper.txt --max-chars 12000   # 截断（LLM 上下文友好）
依赖：pip install pypdf
"""
import argparse
import sys
from pathlib import Path


def extract(pdf_path, max_chars=0):
    try:
        from pypdf import PdfReader
    except ImportError:
        print("缺依赖：python -m pip install pypdf", file=sys.stderr)
        raise SystemExit(2)
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        pages.append(f"\n\n===== [第 {i + 1} 页 / 共 {len(reader.pages)} 页] =====\n\n{page.extract_text() or ''}")
    text = "".join(pages)
    if max_chars and len(text) > max_chars:
        text = text[:max_chars] + f"\n\n……[已截断：全文 {len(text)} 字符，保留前 {max_chars}]"
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--max-chars", type=int, default=0)
    a = ap.parse_args()
    text = extract(a.pdf, a.max_chars)
    Path(a.out).write_text(text, encoding="utf-8")
    print(f"[paper_text] {len(text)} 字符 -> {a.out}")


if __name__ == "__main__":
    main()
