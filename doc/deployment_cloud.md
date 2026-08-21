# GalaCredit 云端部署与运维说明

## 1. 生产入口

- H5：`https://galacredit.ebamotor.com`
- 管理后台：`https://gala.ebamotor.com`
- 服务器：`66.94.122.149`

## 2. 运行隔离

- GalaCredit 后端容器：`galacredit-backend`
- 后端监听：`127.0.0.1:28002`（通过 Caddy 对外提供 HTTPS）
- H5 静态目录：`/data/www/galacredit`
- 管理后台静态目录：`/data/www/gala.ebamotor.com`
- 应用代码目录：`/opt/galacredit/backend`
- 独立数据库：`galacredit`
- 不得将 GalaCredit 配置为连接 `xiaohebao` 数据库。

## 3. Caddy 配置

配置文件：`/opt/talking202605/cloud-deploy/caddy/Caddyfile`

修改前备份，校验后仅 reload：

```bash
cp /opt/talking202605/cloud-deploy/caddy/Caddyfile /opt/talking202605/cloud-deploy/caddy/Caddyfile.bak-$(date +%Y%m%d%H%M%S)
docker exec talking202605-caddy caddy validate --config /etc/caddy/Caddyfile
docker exec talking202605-caddy caddy reload --config /etc/caddy/Caddyfile
```

禁止重启整个 Docker 编排、安装新的 Nginx、占用 80/443 或重启其他业务容器。

## 4. 后端维护

```bash
docker ps --filter name=galacredit-backend
docker logs --tail 100 galacredit-backend
curl http://127.0.0.1:28002/
docker restart galacredit-backend
```

后端配置文件：`/opt/galacredit/backend/.env`。该文件包含密钥，禁止提交 Git、复制到工单或粘贴到聊天记录。

## 5. 前端发布

本地构建管理端后，将 `frontend_admin/dist` 的内容发布到 `/data/www/gala.ebamotor.com`；H5 构建产物发布到 `/data/www/galacredit`。发布后验证：

```bash
curl -I https://gala.ebamotor.com/
curl -I https://galacredit.ebamotor.com/
curl -I https://galacredit.ebamotor.com/manifest.webmanifest
```

## 6. 数据库与账号

GalaCredit 仅使用 `galacredit` 库。当前超级管理员为 `xiaojiang`，账号密码应通过安全渠道交付并定期修改。禁止在数据库、日志和 Git 中保存明文密码。

## 7. 故障排查顺序

1. 检查 DNS 是否指向 `66.94.122.149`。
2. 检查 `galacredit-backend` 是否运行及端口 28002。
3. 检查 Caddy validate 和 reload 输出。
4. 检查浏览器是否缓存旧的 `index.html`，执行强制刷新。
5. 检查旧服务容器状态，避免扩大操作范围。
