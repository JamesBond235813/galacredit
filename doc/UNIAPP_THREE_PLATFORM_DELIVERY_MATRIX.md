# GalaCredit UniApp 三端交付矩阵

## 目标与平台边界

| 能力 | H5 | Android | iOS | 当前证据 |
|---|---|---|---|---|
| 统一 UniApp 业务页面 | 已有 | WebView/UniApp 入口 | WKWebView/UniApp 入口 | `frontend_uniapp/src/pages`、原生壳加载 H5 |
| 用户授权后短信风控 | 浏览器不提供系统短信读取；支持用户主动提供内容的替代方案 | 内部包在单独同意和系统 READ_SMS 授权后读取，设备端关键词过滤 | iOS 不提供系统短信数据库读取 API；使用验证码或用户主动提供内容 | `src/utils/sms.js`、`android_native/.../NativeWebViewActivity.java`、`ios_native/Sources/.../APIClient.swift` |
| 设备基础信息 | 已有 | 已有原生摘要桥 | 已有最小摘要桥 | `src/utils/risk.js`、`platform.js` |
| 定位 | 用户主动触发一次性定位 | UniApp/原生权限 | Core Location 桥 | `src/pages/location`、`platform.js`、iOS `H5HomeView.swift` |
| 身份图片 | 文件选择/上传 | WebView 文件选择 | 原生图片选择桥 | `src/pages/verification`、`platform.js`、原生壳 |
| 原生包构建 | H5 构建可执行 | 需要 HBuilderX/UniApp CLI | 需要完整 Xcode | `scripts/build-app.sh` |

## 已验证

- UniApp：31 项测试通过，H5 生产构建通过。
- Android 控制台：17 项测试通过。
- Android 短信关键词源：173 个关键词同步检查通过。
- Android 渠道检查：Play 包与内部包的短信权限/关键词资产隔离检查通过。
- 后端数据库：4 个迁移版本已应用，32 张表。

## 交付前必须关闭

1. 在安装 HBuilderX/UniApp CLI 的环境生成并验收 Android app-plus 包。
2. 在安装完整 Xcode 的 macOS 环境编译、签名并验收 iOS 包。
3. 完成 H5 主流程、Android 内部短信授权流程、iOS 降级采集流程的真机验收。
4. 修复或更新后端 15 项失败回归测试，使测试契约与当前业务实现一致。
5. 对所有页面执行真实接口、弱网、超时、重复提交和生命周期恢复验证。
