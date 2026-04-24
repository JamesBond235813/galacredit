# 建议命令

## 通用（Darwin/macOS）
- `ls -la` 查看目录
- `cd <path>` 切换目录
- `rg <pattern>` 全局搜索文本
- `rg --files` 列出文件
- `find . -name "<name>"` 按名称查找
- `git status` 查看变更
- `git diff` 查看差异

## 后端（在 `backend/`）
- 安装依赖: `pip install -r requirements.txt`
- 本地启动（推荐）: `uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
- 备选启动: `python app/main.py`

## 用户端 H5（在 `frontend_h5/`）
- 安装依赖: `npm install`
- 开发: `npm run dev`
- 构建: `npm run build`
- 预览: `npm run preview`

## 管理端（在 `frontend_admin/`）
- 安装依赖: `npm install`
- 开发: `npm run dev`
- 构建: `npm run build`
- 预览: `npm run preview`

## 当前仓库现状
- 暂未发现明确 lint/test 脚本（package.json 中仅有 dev/build/preview）。