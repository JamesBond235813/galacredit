# GalaCredit 三端发布清单

## H5

1. 复制 `.env.example` 为 `.env.production` 并确认 API 地址。
2. 执行 `npm ci && npm run test && npm run build:h5`。
3. 将 `dist` 部署到 HTTPS 域名，并配置 `/api` 反向代理。

## Android

- 内部 APK：使用独立包名 `com.galacredit.app.internal`，执行 `GALA_SMS_COLLECTION_ENABLED=true GALA_APPLICATION_ID=com.galacredit.app.internal android_native/build_apk.sh debug`；产物位于 `android_native/build/com.galacredit.app.internal/debug/`。
- Google Play：使用正式包名 `com.galacredit.app`，产物必须是 AAB，启用 Play App Signing、Play Billing 和 FCM。
- 短信边界：页面同意值、原生桥接、manifest 权限和服务端渠道校验必须同时通过；Play 包、iOS 和 H5 均不得读取短信，当前版本也不得上传完整应用列表。
- 发布前执行 `android_native/release_check.sh play`，并核对隐私政策、金融服务披露和权限声明。

## iOS

- Bundle Identifier：`com.galacredit.ios`。
- 使用 Xcode Archive 生成 IPA，并配置 Apple Distribution certificate、provisioning profile 和 APNs。
- 审核前核对隐私权限文案、Sign in with Apple（如提供第三方登录）和数字商品支付规则。
