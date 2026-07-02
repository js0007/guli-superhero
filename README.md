# 古力小超人 · 妈妈版带读

孩子看纸质书，妈妈用手机当带读小抄。仅部署 `site/` 目录即可上线。

## 目录结构

```
古力小超人/
├── 原始素材/          # 图片、音频、Word 文稿（不部署）
├── 需求描述/
├── data/content/      # 带读 JSON 源数据
├── scripts/           # 构建脚本
└── site/              # ★ 部署此目录
    ├── index.html     # 书架首页
    ├── assets/        # 共用 CSS/JS/logo
    ├── templates/
    └── books/         # 各册带读页
```

## 构建

```powershell
# 仅重建站点（使用现有 data/content）
python scripts/build_all.py

# 从 Word 重新提取英文 → 翻译 → 丰富指导 → 构建站点
python scripts/build_daidu.py all
```

分步命令：

```powershell
python scripts/build_daidu.py extract    # → data/content/en/
python scripts/translate_content.py      # → data/content/
python scripts/enrich_guides.py          # 优化互动指导
python scripts/build_all.py              # → site/
```

## 本地预览

```powershell
cd site
python -m http.server 8080
```

浏览器打开 http://localhost:8080

## GitHub Pages 部署

1. 运行 `python scripts/build_all.py`
2. 提交并推送到 GitHub
3. 仓库 **Settings → Pages → Build and deployment**
4. Source 选 **GitHub Actions**（工作流 `.github/workflows/pages.yml` 会自动发布 `site/`）
5. 推送后打开 **Actions** 页，等 Deploy 变绿，即可访问站点 URL

> 说明：GitHub 分支部署只支持根目录或 `/docs`，本项目用 Actions 发布 `site/` 子目录。

## 依赖
- `pip install deep-translator`（翻译步骤需要）
- 读取 `.doc` 需要 `pip install pywin32`（仅 Windows）
