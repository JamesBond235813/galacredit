#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/frontend_admin"

# 构建并部署管理端到腾讯云 (152.136.236.144)，nginx 站点 xhbadmin.juxin.pro
# 注意：--exclude download 用于保护服务器上的安卓 APK 下载目录(/dist/download)，切勿删除
pnpm build
rsync -avzc --delete --progress ./dist/ tencent-superapi:/data/www/xhbadmin.juxin.pro/dist/ \
  --exclude "download"
