# GalaCredit iOS Codex 交接说明

## 目标

这份文档给另一台主机上的 Codex 使用。目标是让接手者打开仓库后，能直接继续 GalaCredit 的 iOS 开发、构建、验收与发布，不需要重新摸索项目结构。

## 当前项目状态

- 仓库根目录：`/Users/jackbond/Desktop/Ghana_loan/GalaCredit`
- 主技术栈：后端 `FastAPI + Uvicorn + asyncio + Pydantic + SQLAlchemy + MySQL 8`，前端 `Vue 3.5 + Vite`，移动端复用 `frontend_uniapp`
- 当前已完成的 UniApp 方向工作：
  - H5、Android、iOS 共用页面和业务状态流
  - 底部胶囊导航，图标在上、文案在下
  - 首页额度展示逻辑
  - Android 应用内升级检查逻辑
  - Android 启动图标已替换为信用卡风格图标
  - iOS 所需隐私权限声明和原生桥接已补齐

## 关键代码入口

- UniApp 主工程：`frontend_uniapp/`
- 页面流转主逻辑：`frontend_uniapp/src/utils/application-flow.js`
- 应用升级逻辑：`frontend_uniapp/src/utils/app-update.js`
- 平台适配：`frontend_uniapp/src/utils/platform.js`
- 底部导航：`frontend_uniapp/src/components/BottomNav.vue`
- H5 外壳：`frontend_uniapp/src/App.h5.vue`
- app-plus 外壳：`frontend_uniapp/src/App.vue`
- 页面路由：`frontend_uniapp/src/pages.json`
- iOS/Android manifest：`frontend_uniapp/manifest.json` 和 `frontend_uniapp/src/manifest.json`
- iOS 构建说明：`doc/ios_build.md`

## 需要优先理解的业务约束

- Home、My Applications、My Account 的入口必须共享同一套状态流，不能出现“同一申请从不同入口跳到不同下一步”的分叉。
- 用户域名的 `/download/*` 必须走真实静态下载，不可回落到 SPA 首页。
- Android 安装包的图标必须来自 `frontend_uniapp/src/static/icons/` 的定制资源，不能再回到默认绿色 H。
- iOS 侧只做必要的系统权限与原生能力适配，不单独拆出另一套业务逻辑。

## 现有验收结论

- `frontend_uniapp` 已通过 Vitest 与构建检查。
- H5 与 Android 的同批次页面逻辑已统一到当前 UniApp 实现。
- 当前生产链路已核对过 H5、管理端、后端、数据库和下载链路，但 iOS 真机验收仍未完成。

## 当前机器的已知阻塞

这台 Mac 目前不适合继续做完整 iOS 发布：

- 只有 Command Line Tools，没有完整 Xcode
- 没有 `simctl`
- 没有可用 iPhone
- 没有完成 Apple Team、证书和 Provisioning Profile 配置
- 磁盘空间此前不足，虽已清理过一部分，但仍不建议在这台机器上继续承担完整 iOS 发行链路

## 另一台主机上应先做的事

1. 安装完整 Xcode，并保证充足磁盘空间。
2. 登录 Apple ID / Apple Developer。
3. 设置开发者目录。

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
xcodebuild -version
xcrun simctl list devices
```

4. 打开 `frontend_uniapp`，核对 `manifest.json`、页面路由和图标资源。
5. 在 HBuilderX 中配置：
   - Apple Team
   - Bundle ID
   - 证书
   - Provisioning Profile
   - 图标与启动图
6. 执行 iOS 云打包或本地发行。
7. 在 Simulator 或真机上逐页验收。

## 首次接手时的检查顺序

1. 先确认仓库当前分支和工作树状态，避免覆盖现有未提交改动。
2. 执行前端测试。

```bash
cd frontend_uniapp
npm test
npm run build:h5
npm run build:uni:app
```

3. 检查 `doc/work_result/` 中最新一条记录，确认最近一次完成了什么。
4. 再决定是继续 iOS 配置、重新打包，还是做真机验收。

## iOS 验收清单

- 登录页是否有状态栏遮挡
- Home / My Applications / My Account 是否保持胶囊导航一致
- 申请流是否从同一状态进入同一下一步
- Ghana Card 上传、相册、相机权限是否正常
- 人脸验证、定位、通讯录权限是否正常
- 申请提交、审核、批准、拒绝、提现、账单的状态切换是否一致
- 键盘弹起时标题和安全区是否被遮挡
- iOS 安装包启动图标是否正确

## 工作规范

- 只做最小改动，不做无关重构。
- 修改后必须补测试。
- 不要泄露密钥、证书、`.env`、JKS 密码。
- 不要回滚别人或之前的未提交修改。
- 每轮完成后都要更新 `doc/work_result/YYYYMMDD.md`。

## 当前建议

下一台主机接手后，优先顺序仍然是：

1. 确认 iOS 开发环境完整可用。
2. 继续 UniApp/iOS 的构建和签名配置。
3. 在真机或模拟器上做逐页验收。
4. 仅在验收发现问题时，再回到源码修复。
