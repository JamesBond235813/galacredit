# 任务完成检查

由于当前仓库未提供统一测试/格式化脚本，完成代码任务后建议至少执行：

1. 后端改动
- 在 `backend/` 安装依赖并启动服务：`uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
- 手工验证相关 API 路由（auth/user/loan/admin）可访问且核心流程正常。

2. 前端改动
- 在对应前端目录运行：`npm run build`（至少保证可构建）
- 需要本地联调时运行：`npm run dev` 手工检查改动页面

3. 提交前
- `git status` 确认改动范围
- `git diff` 自查是否包含无关变更
- 若引入新命令/流程，补充文档说明（README 或项目文档）