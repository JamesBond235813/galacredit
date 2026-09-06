#!/usr/bin/env bash
set -euo pipefail

# 统一 app-plus 资源构建入口；原生 APK 仍由 HBuilderX/运行基座负责签名与安装。
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
command -v adb >/dev/null 2>&1 || { echo '缺少 adb，请安装 Android SDK Platform Tools' >&2; exit 2; }
test -d "${ANDROID_HOME:-$HOME/Library/Android/sdk}" || { echo '缺少 Android SDK' >&2; exit 2; }
npm exec -- uni build -p app-plus
test -s dist/build/app/app-service.js
test -s dist/build/app/app-config.js
test -s dist/build/app/__uniappview.html
expected_pages="$(node -e "const p=require('./src/pages.json'); process.stdout.write(String(p.pages.length))")"
actual_pages="$(find dist/build/app/pages -name '*.css' | wc -l | tr -d ' ')"
test "$actual_pages" = "$expected_pages" || { echo "app-plus 页面产物数量不一致：期望 $expected_pages，实际 $actual_pages" >&2; exit 3; }
echo "app-plus 资源构建完成：$ROOT_DIR/dist/build/app"
echo '下一步：使用 HBuilderX 导入 frontend_uniapp，选择 Android app-plus 真机运行或发行。'
