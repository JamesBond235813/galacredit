# GalaCredit 三端发布清单

## H5

1. 复制 `.env.example` 为 `.env.production` 并确认 API 地址。
2. 执行 `npm ci && npm run test && npm run build:h5`。
3. 将 `dist` 部署到 HTTPS 域名，并配置 `/api` 反向代理。

## Android

### UniApp app-plus 标准包

1. 执行 `npm ci && npm test && bash scripts/build-app-plus.sh`，确认 19 个页面资源全部生成。
2. 登录 HBuilderX 的 DCloud 账号后执行 `bash scripts/pack-app-plus.sh`；也可通过“发行 → App-Android/iOS-云打包”操作。脚本使用安心打包（本机签名），避免传统云端签名失败。当前采用同签名 JKS 兼容证书用于手机覆盖升级，不是新创建的上架证书。私钥放在被忽略的 `frontend_uniapp/.local/` 中，勿提交。
3. Android 云打包过程中不要同时运行默认 H5 构建（会清理 dist）；H5 独立验证用 `npm run build:h5 -- --outDir /tmp/galacredit-h5-check`。选择 APK 或 AAB 输出；安装前先在三星真机验证登录、协议、验证码和页面路由。
4. app-plus 包使用 `src/utils/platform.js` 的 UniApp 原生能力；短信、定位、相册等权限必须与渠道策略一致。

- 内部 APK：使用独立包名 `com.galacredit.app.internal`，在 HBuilderX/UniApp app-plus 构建中选择内部渠道配置；产物为 APK。
- Google Play：使用正式包名 `com.galacredit.app`，产物必须是 AAB，启用 Play App Signing、Play Billing 和 FCM。
- 短信边界：页面同意值、原生桥接、manifest 权限和服务端渠道校验必须同时通过；Play 包、iOS 和 H5 均不得读取短信，当前版本也不得上传完整应用列表。
- 发布前依据 `channel-config.json` 核对 Play AAB、Play App Signing、隐私政策、金融服务披露和权限声明。

## iOS

- Bundle Identifier：`com.galacredit.ios`。
- 使用 Xcode Archive 生成 IPA，并配置 Apple Distribution certificate、provisioning profile 和 APNs。
- 审核前核对隐私权限文案、Sign in with Apple（如提供第三方登录）和数字商品支付规则。
