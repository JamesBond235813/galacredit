# GalaCredit uni-app 三端工程

该目录是 H5、Android、iOS 共用的迁移目标工程。页面和业务逻辑统一，平台差异集中在 `src/utils` 与 `src/api`。

## 发行目标

- H5：`VITE_API_BASE_URL` 配置后执行 uni-app H5 构建。
- Android 非上架版：生成 APK，使用独立测试包名/签名。
- Google Play：生成 AAB，固定正式包名 `com.galacredit.app`，使用 Play App Signing。
- iOS：使用正式 Bundle Identifier 和 App Store 签名发布。

Android 两个版本不维护两套业务代码；仅通过 flavor、签名、包名和支付/推送能力配置区分。

## 构建

```bash
npm install
npm run dev:h5
npm run build:h5
npm run build:app
```

`build:app` 会自动探测 HBuilderX/uni-app CLI；未安装时给出明确诊断。该命令需要 Android SDK、Xcode 和签名环境；渠道差异见 `../android_native/channel-config.json`。

完整发布前检查见 [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md)。
