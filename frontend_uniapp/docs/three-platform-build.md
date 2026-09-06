# GalaCredit 三端构建与安装

```bash
npm install
npm run build:uni:h5
npm run build:uni:app
```

`pages.json` 是三端页面注册入口，业务页面位于 `src/pages`。只有 Internal Android 在用户勾选短信授权并通过系统权限后读取短信；设备端按关键词过滤并仅提交 90 天内命中项。Google Play、iOS 和 H5 不读取系统短信数据库，只处理用户主动提供内容或验证码。

iOS 真机需要完整 Xcode、有效 Team/Bundle ID、provisioning profile，以及解锁并信任电脑的设备。Command Line Tools 不能替代 Xcode 的 iOS 编译、签名和安装能力。
