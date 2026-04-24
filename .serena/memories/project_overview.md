# xiaohebao 项目概览（已按最新文件重读）

## 目的
信贷/小额贷款业务系统，包含用户侧 H5、管理后台、FastAPI 后端。

## 技术栈
- 后端: Python 3.9 + FastAPI + Uvicorn + SQLAlchemy + MySQL + APScheduler + JWT
- 前端用户端: Vue 3 + Vite + Vue Router + Pinia + Vant + Axios
- 前端管理端: Vue 3 + Vite + Vue Router + Element Plus + Axios

## 关键目录
- `backend/`: API 服务、模型、schema、业务服务
- `frontend_h5/`: 用户端 H5
- `frontend_admin/`: 管理后台
- `doc/`: 业务/接口补充文档（包含 `E签宝接口文档.txt`）
- `AGENTS.md`: 当前仓库的强约束开发规范（新增且重要）

## 当前仓库状态
- Git 未跟踪文件：`frontend_h5/pnpm-lock.yaml`
- 根 `README.md` 仍为模板型内容，项目约束以 `AGENTS.md` 为准。