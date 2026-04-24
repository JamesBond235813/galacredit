# 建议命令（最新版）

## 通用（macOS/Darwin）
- `ls -la`
- `cd <path>`
- `rg <pattern>`
- `rg --files`
- `find . -name "<name>"`
- `git status`
- `git diff`

## 后端（`backend/`）
- 安装依赖：`pip install -r requirements.txt`
- 启动（项目规范要求）：`python -m app.main`
- 备选启动：`uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`

## 前端 H5（`frontend_h5/`）
- 安装依赖：`npm install`
- 开发：`npm run dev`
- 构建：`npm run build`
- 预览：`npm run preview`

## 前端管理端（`frontend_admin/`）
- 安装依赖：`npm install`
- 开发：`npm run dev`
- 构建：`npm run build`
- 预览：`npm run preview`

## 备注
- 当前 package.json 中未声明 lint/test 脚本；执行测试流程时需要按实际测试文件与框架手动组织命令。