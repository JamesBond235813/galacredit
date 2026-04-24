# xiaohebao 项目概览

## 目的
一个信贷/小额贷款业务系统，包含用户侧 H5 申请流程、管理后台、以及 FastAPI 后端接口。

## 技术栈
- 后端: Python + FastAPI + SQLAlchemy + MySQL + APScheduler + JWT
- 前端用户端: Vue 3 + Vite + Vue Router + Pinia + Vant + Axios
- 前端管理端: Vue 3 + Vite + Vue Router + Element Plus + Axios

## 代码结构
- `backend/`: FastAPI 服务
  - `app/main.py`: 应用入口（含 CORS、生命周期初始化、路由挂载）
  - `app/api/endpoints/`: auth/user/loan/admin 各业务接口
  - `app/models/`: SQLAlchemy 模型
  - `app/schemas/`: Pydantic schema
  - `app/services/`: 业务服务（放款、风控、台账、调度等）
  - `app/core/`: 配置、数据库、鉴权
- `frontend_h5/`: 用户端 H5
  - `src/views/`: 页面
  - `src/api/`: 请求封装与接口
  - `src/router/`: 路由
- `frontend_admin/`: 管理后台
  - `src/views/`: 后台页面
  - `src/api/`: 请求封装与接口
  - `src/router/`: 路由

## 入口
- 后端入口模块: `backend/app/main.py`
- 前端入口: `frontend_h5/src/main.js`, `frontend_admin/src/main.js`