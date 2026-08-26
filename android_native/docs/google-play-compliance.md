# GalaCredit Android Google Play 上架审查清单

## 已完成的代码侧修正

- `targetSdkVersion` 已提升到 35，`versionCode` 为 26，`versionName` 为 0.3.0。
- 删除 `READ_SMS`：普通借贷应用不应申请 Google Play 受限短信权限。
- 删除 `REQUEST_INSTALL_PACKAGES`、APK Provider 和自动更新入口：Google Play 分发应由 Play 管理更新，不应在 App 内安装外部 APK。
- 风控上报不再读取短信全文或已安装应用清单，仅保留设备基础信息、Android ID 哈希/设备完整性摘要等最小化信号。
- 保留定位权限，但必须在实际需要定位的页面前通过清晰说明和系统权限弹窗取得授权。
- 继续使用 HTTPS、应用内 WebView、最小化 exported 组件。

## 上架前必须由运营/法务确认

1. 在 Play Console 的 App content 中填写真实开发者、隐私政策 URL、数据安全表单和金融服务声明。
2. 如果提供信贷/借款服务，填写 Financial features declaration，并确认目标国家、贷款 APR、费用、还款期限和许可信息与实际业务一致。
3. 隐私政策必须明确说明：手机号、验证码、定位、设备信息、登录日志、风控用途、保存期限、共享对象、删除/撤回方式和客服联系方式。
4. 商店描述、截图、应用内文案不能承诺“保证放款”“无条件通过”等误导性结果。
5. 提供真实测试账号/测试流程给审核团队；验证码服务需能在审核环境稳定工作。
6. 正式发布必须使用 Play App Signing；不要上传 debug keystore 或自签测试 APK。
7. 完成 Data safety 与权限声明后，再通过 Internal testing、Pre-launch report 和 closed testing 验证崩溃、WebView、定位授权及登录流程。

## 当前仍需外部材料

- 公开可访问的 GalaCredit 隐私政策 URL。
- 公司主体、加纳业务许可及金融服务披露材料。
- 正式 release keystore / Play App Signing 配置。
- 商店图标、Feature graphic、手机截图、内容分级和目标国家配置。
