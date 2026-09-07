# GalaCredit UniApp iOS 构建说明

当前 iOS 客户端复用 `frontend_uniapp` 的页面、状态流、接口和交互代码。Android 与 H5 已使用同一套页面图；iOS 专属部分只保留系统权限和原生能力适配。

## 本地发行前检查

```bash
cd frontend_uniapp
npm install
npm test -- --run
npm run build:uni:app
```

在 HBuilderX 中导入 `frontend_uniapp`，选择“发行 → 原生 App-云打包 → iOS”。正式发行前填写：

- Bundle ID：使用 Apple Developer 中已注册的 GalaCredit App ID
- Apple Team、签名证书和 Provisioning Profile
- App 图标与启动图
- `versionName` 与 `versionCode`

## iOS 权限

`manifest.json` 已声明相机、定位、相册和通讯录用途，分别对应身份认证、位置检查、证件照片选择和紧急联系人选择。

## 真机验收顺序

1. 登录并确认 Home、My Applications、My Account 三个 Tab 的胶囊导航。
2. 从 Home 和 My Applications 进入申请，确认 INIT 状态都进入 Ghana Card 身份验证。
3. 依次验证相册/相机、活体、人脸失败重试、紧急联系人、位置检查和提交申请。
4. 使用后台账号切换 REVIEWING、APPROVED、REJECTED、DISBURSED 状态，逐一验证下一页一致。
5. 在 iOS 设置中撤销相机、相册、定位和通讯录权限，再重复操作，确认页面显示可理解的失败提示并可重试。

当前开发机只有 CommandLineTools，没有完整 Xcode，因此签名、Archive、Simulator 和 iPhone 安装必须在具备 Xcode 的 Mac 上完成。
