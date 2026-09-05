# GalaCredit 原生安卓用户端 App

## 当前产物

- App 名称：GalaCredit
- 包名：`com.galacredit.app`
- 生产接口：`https://galacredit.ebamotor.com/api`
- 本地调试包：`android_native/build/com.galacredit.app/debug/galacredit-debug.apk`
- 正式签名包：`android_native/build/com.galacredit.app/release/galacredit-release.apk`
- Google Play 正式包由 Play Console 分发；仅测试包可通过内部下载渠道分发。

## 已实现能力

- 用户手机号验证码登录。
- 登录后调用 `/api/user/info`、`/api/loan/status`、`/api/loan/products` 获取用户授信、订单和产品信息。
- 首页按用户借款状态展示申请、审核、提现、账单等用户端入口。
- 登录前展示用户协议、隐私政策和个人信息授权确认。
- 受信任业务 WebView 提供一次性短信风险复核桥接：只有内部包、用户主动勾选并通过系统 `READ_SMS` 授权后，原生层读取最近 90 天并按关键词过滤，再将最小结果异步回传页面。
- 短信桥接在运行时同时校验 `.internal` 包名和 manifest 权限；即使页面误传同意参数或 Play 包被错误配置，也不会触发短信读取。
- 生产版本不在 App 内下载或安装 APK，由 Google Play 管理更新。

## 本地构建

```bash
cd "/Users/littlejiang/Desktop/galacredit/android_native"
./build_apk.sh
```

构建成功后输出：

```text
android_native/build/com.galacredit.app/debug/galacredit-debug.apk
```

## 安装到手机

```bash
adb install -r android_native/build/com.galacredit.app/debug/galacredit-debug.apk
```

## 正式发布

- 构建正式包：

```bash
cd "/Users/littlejiang/Desktop/galacredit/android_native"
./build_apk.sh release
```

- 正式发布必须使用 Play App Signing，并通过 Internal/Closed testing 逐步发布。

## 短信风控内部构建

内部、具备明确用户授权且不提交 Google Play 的构建可以启用短信最小化采集：

```bash
GALA_SMS_COLLECTION_ENABLED=true GALA_APPLICATION_ID=com.galacredit.app.internal ./build_apk.sh debug
```

该构建会声明 `READ_SMS`，登录后仅在用户勾选短信授权并通过系统权限弹窗后，读取最近 90 天短信，按 `sms_keys20260602.csv` 过滤后上传命中项。需要内部专用包名时同时设置 `GALA_APPLICATION_ID=com.galacredit.app.internal`。Google Play 构建不要设置短信变量，正式包名保持 `com.galacredit.app`。

登录后“Security review”页面也可通过 `GalaCreditRisk.startSmsReview` 请求一次性复核；桥接只返回已完成本地过滤的最小短信集合，不返回未过滤的短信数据库内容。若用户拒绝权限、包未声明权限或桥接超时，页面继续使用设备和账户风险信号，不阻断贷款流程。
