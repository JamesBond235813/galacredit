# GalaCredit 原生安卓用户端 App

## 当前产物

- App 名称：GalaCredit
- 包名：`com.galacredit.app`
- 生产接口：`https://galacredit.ebamotor.com/api`
- 本地调试包：`android_native/build/galacredit-debug.apk`
- 正式签名包：`android_native/build/galacredit-release.apk`
- Google Play 正式包由 Play Console 分发；仅测试包可通过内部下载渠道分发。

## 已实现能力

- 用户手机号验证码登录。
- 登录后调用 `/api/user/info`、`/api/loan/status`、`/api/loan/products` 获取用户授信、订单和产品信息。
- 首页按用户借款状态展示申请、审核、提现、账单等用户端入口。
- 登录前展示用户协议、隐私政策和个人信息授权确认。
- 生产版本不在 App 内下载或安装 APK，由 Google Play 管理更新。

## 本地构建

```bash
cd "/Users/littlejiang/Desktop/galacredit/android_native"
./build_apk.sh
```

构建成功后输出：

```text
android_native/build/galacredit-debug.apk
```

## 安装到手机

```bash
adb install -r android_native/build/galacredit-debug.apk
```

## 正式发布

- 构建正式包：

```bash
cd "/Users/littlejiang/Desktop/galacredit/android_native"
./build_apk.sh release
```

- 正式发布必须使用 Play App Signing，并通过 Internal/Closed testing 逐步发布。
