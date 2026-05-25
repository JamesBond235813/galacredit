# 小荷包原生安卓 App

## 当前产物

- App 名称：小荷包
- 包名：`com.juxin.xiaohebao.admin`
- 生产接口：`https://xhbadmin.juxin.pro/api`
- 本地调试包：`android_native/build/xiaohebao-debug.apk`
- 正式签名包：`android_native/build/xiaohebao-release.apk`
- 线上下载地址：`https://xhbadmin.juxin.pro/download/xiaohebao.apk`

## 已实现能力

- 管理后台账号登录。
- 登录后调用 `/api/admin/me` 获取当前管理员角色。
- 根据角色展示移动端业务入口：档案、申请、发卡、回款、平账。
- 支持客户/订单列表搜索。
- 支持与管理后台一致的核心操作：审批、发卡、回款跟进、催收、平账、授信调整、拉黑、解除位置风控等。

## 本地构建

```bash
cd "/Volumes/littlejiang02/VibeCoding/xiaohebao /android_native"
./build_apk.sh
```

构建成功后输出：

```text
android_native/build/xiaohebao-debug.apk
```

## 安装到手机

```bash
/Users/littej/Library/Android/sdk/platform-tools/adb install -r android_native/build/xiaohebao-debug.apk
```

## 正式发布

- release keystore 保存在本机私有目录，不进入仓库：`~/.xiaohebao/android/xiaohebao-release.jks`。
- release 签名环境变量保存在本机私有目录，不进入仓库：`~/.xiaohebao/android/release-signing.env`。
- 构建正式包：

```bash
source ~/.xiaohebao/android/release-signing.env
cd "/Volumes/littlejiang02/VibeCoding/xiaohebao /android_native"
./build_apk.sh release
```

- 生产下载文件名：`xiaohebao.apk`。
- 生产下载地址：`https://xhbadmin.juxin.pro/download/xiaohebao.apk`。
- 安卓系统不允许网页静默安装 APK，用户下载后仍需手动确认安装。
