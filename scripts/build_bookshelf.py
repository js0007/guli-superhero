# -*- coding: utf-8 -*-
"""生成书架首页 site/index.html"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BOOKS = SITE / "books"
ROWS = 4


def book_display(folder: str) -> str:
    return folder.split("_", 1)[1] if "_" in folder else folder


def collect_books() -> list[dict]:
    books = []
    if not BOOKS.is_dir():
        return books
    for folder in sorted(os.listdir(BOOKS)):
        book_dir = BOOKS / folder
        if not book_dir.is_dir():
            continue
        cover = f"books/{folder}/images/0-1.jpg"
        if not (SITE / cover).exists():
            continue
        title = book_display(folder)
        content = book_dir / "content.json"
        if content.exists():
            try:
                title = json.loads(content.read_text(encoding="utf-8")).get("book", title)
            except json.JSONDecodeError:
                pass
        books.append({
            "folder": folder,
            "title": title,
            "cover": cover,
            "href": f"books/{folder}/",
        })
    return books


def book_card(b: dict) -> str:
    return f"""            <a class="book-card" href="{b['href']}" title="{b['title']}">
              <div class="cover-wrap">
                <img class="cover" src="{b['cover']}" alt="{b['title']}">
              </div>
              <div class="book-title">{b['title']}</div>
            </a>"""


def shelf_tier(chunk: list[dict]) -> str:
    cards = "\n".join(book_card(b) for b in chunk)
    return f"""        <div class="shelf-tier">
          <div class="shelf-books">
{cards}
          </div>
          <div class="shelf-plank"></div>
        </div>"""


def build_html(books: list[dict]) -> str:
    tiers = "\n".join(
        shelf_tier(books[i : i + ROWS]) for i in range(0, len(books), ROWS)
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>古力小超人 · 妈妈版带读</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --font-en: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --wall: #F3EBE0;
      --wall-deep: #E8DDD0;
      --cream: #FDF9F3;
      --text-en: #3D3429;
      --text-muted: #9A8B7A;
      --wood-light: #E8D5B8;
      --wood: #D4B896;
      --wood-mid: #C4A57A;
      --plank: #C9A876;
      --page-pad: clamp(10px, 3.5vw, 22px);
      --cabinet-pad: clamp(10px, 2.8vw, 18px);
      --book-gap: clamp(5px, 1.8vw, 12px);
      --title-size: clamp(0.54rem, 2.6vw, 0.68rem);
      --head-title: clamp(0.82rem, 3.8vw, 1rem);
      --slogan-size: clamp(0.68rem, 3.2vw, 0.82rem);
    }}

    html, body {{
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      background: linear-gradient(180deg, var(--wall) 0%, var(--wall-deep) 100%);
      color: var(--text-en);
      min-height: 100dvh;
    }}

    .app {{
      width: 100%;
      max-width: min(100%, 720px);
      margin: 0 auto;
      min-height: 100dvh;
      padding: 0 var(--page-pad) clamp(16px, 4vw, 32px);
    }}

    .top-bar {{
      display: flex;
      align-items: flex-start;
      gap: clamp(8px, 2.5vw, 14px);
      margin: 0 calc(var(--page-pad) * -0.35);
      padding: clamp(10px, 3vw, 16px) clamp(12px, 3.5vw, 18px) clamp(12px, 3.5vw, 16px);
      background: var(--cream);
      border-radius: 0 0 clamp(14px, 4vw, 22px) clamp(14px, 4vw, 22px);
      box-shadow: 0 4px 16px rgba(80, 55, 30, 0.08);
      position: sticky;
      top: 0;
      z-index: 10;
    }}

    .top-logo {{
      flex-shrink: 0;
      height: clamp(32px, 9vw, 42px);
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 1px 2px rgba(0,0,0,0.08));
      margin-top: 2px;
    }}

    .top-head {{
      flex: 1;
      min-width: 0;
    }}

    .top-title {{
      font-family: var(--font-en);
      font-weight: 800;
      font-size: var(--head-title);
      color: var(--text-en);
      line-height: 1.25;
      letter-spacing: -0.01em;
    }}

    .top-slogan {{
      display: flex;
      align-items: flex-start;
      gap: 4px;
      margin-top: clamp(4px, 1.2vw, 8px);
      font-size: var(--slogan-size);
      color: var(--text-muted);
      line-height: 1.45;
    }}

    .slogan-spark {{
      flex-shrink: 0;
      color: #D4A84B;
      font-size: 0.95em;
      line-height: 1.35;
      opacity: 0.9;
    }}

    .bookshelf-wrap {{
      padding-top: clamp(14px, 4vw, 24px);
    }}

    .bookshelf-cabinet {{
      width: 100%;
      max-width: 640px;
      margin: 0 auto;
      background: linear-gradient(165deg, var(--wood-light) 0%, var(--wood) 45%, var(--wood-mid) 100%);
      border-radius: clamp(14px, 4vw, 22px);
      padding: var(--cabinet-pad);
      box-shadow:
        0 10px 28px rgba(70, 45, 20, 0.18),
        inset 0 2px 0 rgba(255, 255, 255, 0.45),
        inset 0 -3px 6px rgba(0, 0, 0, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.25);
    }}

    .shelf-tier:last-child .shelf-plank {{
      border-radius: 0 0 6px 6px;
    }}

    .shelf-books {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: var(--book-gap);
      padding: clamp(4px, 1.5vw, 8px) clamp(2px, 1vw, 6px) 0;
      align-items: end;
    }}

    .shelf-plank {{
      height: clamp(10px, 2.8vw, 16px);
      margin: 0 2px;
      border-radius: 3px;
      background: linear-gradient(180deg, #DEC9A8 0%, var(--plank) 40%, #B89568 100%);
      box-shadow:
        0 4px 8px rgba(60, 40, 20, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.35);
    }}

    .shelf-tier + .shelf-tier {{
      margin-top: clamp(8px, 2.5vw, 14px);
    }}

    .book-card {{
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
      min-width: 0;
      text-decoration: none;
      color: inherit;
      transform-origin: bottom center;
      transition: transform 0.18s ease;
    }}

    .book-card:active {{
      transform: translateY(-4px) scale(1.03);
    }}

    .cover-wrap {{
      position: relative;
      width: 100%;
      height: 0;
      padding-bottom: 100%;
      overflow: hidden;
      flex-shrink: 0;
      background: #fff;
      border-radius: clamp(4px, 1.2vw, 8px) clamp(6px, 1.8vw, 10px) clamp(3px, 1vw, 6px) clamp(3px, 1vw, 6px);
      box-shadow:
        3px 4px 10px rgba(0, 0, 0, 0.16),
        1px 1px 0 rgba(255, 255, 255, 0.5) inset,
        -3px 0 6px rgba(0, 0, 0, 0.07) inset;
      border: 1px solid rgba(255, 255, 255, 0.6);
    }}

    .cover-wrap::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 5px;
      background: linear-gradient(90deg, rgba(0,0,0,0.12) 0%, rgba(0,0,0,0.03) 100%);
      border-radius: 6px 0 0 4px;
      z-index: 1;
      pointer-events: none;
    }}

    .cover {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center center;
      display: block;
    }}

    .book-title {{
      margin-top: 6px;
      padding: 3px 6px;
      width: 100%;
      box-sizing: border-box;
      font-family: var(--font-en);
      font-weight: 600;
      font-size: var(--title-size);
      color: var(--text-en);
      text-align: center;
      line-height: 1.2;
      background: var(--cream);
      border-radius: 999px;
      border: 1px solid rgba(200, 175, 140, 0.45);
      box-shadow: 0 2px 4px rgba(60, 40, 20, 0.08);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
  </style>
</head>
<body>
  <div class="app">
    <header class="top-bar">
      <img class="top-logo" src="assets/logo.png" alt="古力小超人陪读">
      <div class="top-head">
        <h1 class="top-title">古力小超人 · 妈妈版带读</h1>
        <p class="top-slogan">
          <span>翻开绘本，开启属于你们的亲子精读时光。</span>
          <span class="slogan-spark" aria-hidden="true">✦</span>
        </p>
      </div>
    </header>

    <main class="bookshelf-wrap">
      <div class="bookshelf-cabinet">
{tiers}
      </div>
    </main>
  </div>
</body>
</html>
"""


def main() -> None:
    books = collect_books()
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(build_html(books), encoding="utf-8")
    print(f"OK    site/index.html  ({len(books)} books)")


if __name__ == "__main__":
    main()
