# 将 site/ 部署到 GitHub Pages（gh-pages 分支）
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
python scripts/build_all.py

$deploy = Join-Path $env:TEMP "guli-pages-deploy"
if (Test-Path $deploy) { Remove-Item -Recurse -Force $deploy }
New-Item -ItemType Directory -Path $deploy | Out-Null
Copy-Item -Path "site\*" -Destination $deploy -Recurse -Force
Set-Location $deploy
git init -b gh-pages
git add .
git commit -m "Deploy site $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git remote add origin https://github.com/js0007/guli-superhero.git
git push -u origin gh-pages --force
Write-Host "Done. https://js0007.github.io/guli-superhero/"
