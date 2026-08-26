# 2026-08-23 20:40:00

## Google Play 安卓上架审查总结

### 修改说明

- 将 Android `targetSdkVersion` 从 34 提升到 35，版本调整为 `0.3.0 / versionCode 26`。
- 删除 `READ_SMS` 权限、短信读取授权弹窗及短信全文/短信关键词采集代码。
- 删除 `REQUEST_INSTALL_PACKAGES`、APK Provider 和 App 内 APK 自动更新入口；正式版本应由 Google Play 管理更新。
- 风控请求保留最小化设备摘要，短信和已安装应用清单固定为空，不再采集完整短信或 App 列表。
- 修正构建脚本默认生产域名为 `galacredit.ebamotor.com`。
- 新增 [google-play-compliance.md](/Users/littlejiang/Desktop/galacredit/android_native/docs/google-play-compliance.md)，记录 Play Console 仍需填写的金融服务、数据安全、隐私政策和商店素材事项。

### 验证结果

- `./android_native/build_apk.sh debug` 构建成功。
- APK 信息：`com.galacredit.app`，`versionCode=26`，`versionName=0.3.0`，`targetSdkVersion=35`。
- APK 仅声明：`INTERNET`、`ACCESS_COARSE_LOCATION`、`ACCESS_FINE_LOCATION`。
- APK 签名校验通过 v1/v2/v3；当前为 debug 签名，不能直接用于生产上架，必须配置 Play App Signing/release 签名。
- 已尝试连接真机安装，但当前 `adb devices` 没有发现设备，因此未完成真机回归。

### 上架前阻塞项

- 尚未配置正式 release keystore / Play App Signing。
- 尚未提供公开隐私政策 URL及 Google Play Data safety 表单内容。
- 金融服务声明、目标国家、许可材料、APR/费用/期限等必须由业务和法务确认后填写。
