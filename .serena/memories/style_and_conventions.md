# 代码风格与约定（以 AGENTS.md 为准）

## 总体原则（强制）
- 最小改动原则：只改当前需求相关代码，禁止无关重构。
- 优先复用现有模块与函数，避免重复造轮子。

## 后端技术与异步规范（强制）
- 项目架构：FastAPI + Uvicorn + Python 3.9。
- 优先 `async/await`，IO 密集逻辑必须 `async def`。
- 禁止“假异步”（`async def` 内没有 `await`）。
- 禁止在异步路由执行阻塞调用。
- IO 规范：
  - HTTP 使用 `httpx.AsyncClient`，禁用 `requests`
  - 等待使用 `asyncio.sleep`，禁用 `time.sleep`
  - DB 仅允许 SQLAlchemy async 模式
  - 文件操作优先 `aiofiles`
- 异步调用必须显式 `await`，禁止遗漏。

## 注释与可读性
- Python 函数/方法注释必须使用 reST 风格，包含 `:param` 与 `:return:`。
- 关键逻辑必须写中文注释，解释“为什么这样做”。
- 函数职责单一，避免深层嵌套，禁止炫技写法。

## 异常与响应规范（强制）
- 401 仅用于登录验证失败。
- 请求进入 Python 并完成业务处理后，HTTP 状态统一返回 200（业务成功/失败由 `code`、`msg` 表达）。
- 业务代码（service/router 依赖/鉴权辅助）仅允许抛 `BizException`。
- 禁止在业务代码中 `raise HTTPException`。
- Router 层只返回成功结果，失败交由全局异常处理器。
- 响应必须使用项目统一响应基类，禁用 FastAPI 默认 `{"detail": ...}` 结构。