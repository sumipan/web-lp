#!/usr/bin/env python3
"""index.html 内の data:image/jpeg|png;base64,... を images/ に切り出し、HTML を相対パスに置換する。"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r"data:image/(jpeg|png);base64,([A-Za-z0-9+/=]+)",
    re.IGNORECASE,
)


def line_number_at(content: str, pos: int) -> int:
    return content[:pos].count("\n") + 1


def main() -> int:
    root = Path(__file__).resolve().parent
    html_path = root / "index.html"
    if not html_path.is_file():
        print("index.html not found", file=sys.stderr)
        return 1

    content = html_path.read_text(encoding="utf-8")
    matches = list(PATTERN.finditer(content))
    if not matches:
        print("No data:image/jpeg|png base64 URIs found", file=sys.stderr)
        return 1

    images_dir = root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    chunks: list[str] = []
    pos = 0

    for i, m in enumerate(matches):
        mime = m.group(1).lower()
        b64 = m.group(2)
        ext = "jpg" if mime == "jpeg" else "png"
        filename = f"image-{i + 1:02d}.{ext}"
        rel_ref = f"images/{filename}"

        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception as e:
            print(f"decode failed for match {i + 1}: {e}", file=sys.stderr)
            return 1

        (images_dir / filename).write_bytes(raw)
        line_no = line_number_at(content, m.start())
        manifest.append(
            {
                "filename": filename,
                "relative_path": rel_ref,
                "size_bytes": len(raw),
                "mime": f"image/{mime}",
                "source_line": line_no,
            }
        )

        chunks.append(content[pos : m.start()])
        chunks.append(rel_ref)
        pos = m.end()

    chunks.append(content[pos:])
    new_html = "".join(chunks)
    html_path.write_text(new_html, encoding="utf-8")

    print(f"Wrote {len(manifest)} images to {images_dir.relative_to(root)}/")
    for row in manifest:
        print(
            f"  {row['filename']}\t{row['size_bytes']} bytes\tline {row['source_line']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
