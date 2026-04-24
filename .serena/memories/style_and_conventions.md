# 代码风格与约定（基于现有代码）

## Python 后端
- 使用 FastAPI 路由分层：`api/endpoints` + `services` + `models` + `schemas`。
- 配置统一在 `app/core/config.py`，通过 `pydantic-settings` 管理。
- 命名以 snake_case 为主，类名使用 PascalCase。
- 有中文注释，偏业务导向注释。

## Vue 前端
- 使用 Vue 3 单文件组件（`.vue`）。
- JS 模块导入使用 ES Module。
- 视图集中在 `src/views`，接口集中在 `src/api`，路由集中在 `src/router`。
- 用户端统一注册 Vant 组件；管理端统一挂载 Element Plus 与图标。

## 当前可见规范边界
- 仓库未体现强制 lint/format 工具配置（未看到 ESLint/Prettier/Ruff/Black 等配置文件与脚本）。
- 建议修改时遵循“与现有文件风格一致”的最小改动原则。