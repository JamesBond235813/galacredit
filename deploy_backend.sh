#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# 部署后端到腾讯云生产服务器 (152.136.236.144, ssh 别名 tencent-superapi)
# 真实代码目录：/opt/xiaohebao/current/backend，由 systemd 服务 xiaohebao-backend.service 运行
rsync -avzc --delete --progress ./backend/ tencent-superapi:/opt/xiaohebao/current/backend/ \
  --exclude "__MACOSX" --exclude "*/venv" --exclude ".venv" --exclude "tests" \
  --exclude "__pycache__" --exclude ".env*" --exclude "uploads" \
  --exclude "logs" --exclude "pytest.ini" --exclude ".pytest_cache"

echo "重启后端服务..."
ssh tencent-superapi "systemctl restart xiaohebao-backend.service && sleep 2 && systemctl is-active xiaohebao-backend.service"
