#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/frontend_h5"

# 构建并部署 H5 前端到腾讯云 (152.136.236.144)，nginx 站点 xhb.juxin.pro
pnpm build
rsync -avzc --delete --progress ./dist/ tencent-superapi:/data/www/xhb.juxin.pro/dist/
