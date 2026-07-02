# -*- coding: utf-8 -*-
"""一键构建可部署的 site/ 目录"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_bookshelf
import build_site


def build(*, content_only: bool = False) -> None:
    if not content_only:
        build_site.build_all()
    build_bookshelf.main()
    print("All done. Deploy the site/ folder.")


def main() -> None:
    parser = argparse.ArgumentParser(description="构建古力小超人妈妈版带读站点")
    parser.add_argument(
        "--content-only",
        action="store_true",
        help="仅重建书架首页（不重新复制书籍资源）",
    )
    args = parser.parse_args()
    build(content_only=args.content_only)


if __name__ == "__main__":
    main()
