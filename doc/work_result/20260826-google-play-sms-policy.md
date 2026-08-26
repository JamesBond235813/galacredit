# 2026-08-26 21:00:00

## Google Play 短信抓取政策调研

### 官方来源

- [Use of SMS or Call Log permission groups](https://support.google.com/googleplay/android-developer/answer/10208820)
- [Financial Services policy](https://support.google.com/googleplay/android-developer/answer/9876821)
- [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170)
- [User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311)

### 关键结论

1. `READ_SMS`、`RECEIVE_SMS` 等属于受限高风险权限；只有默认短信/电话/助手处理器等核心功能，或政策列明的极少数例外，才可能申请并通过审核。必须先在 Play Console 提交 Permissions Declaration Form，且受 Google Play 逐案审核。
2. 普通借贷、个人贷款、预算管理、风控或用户画像不是“读取用户全部短信”的通用豁免理由。官方将“SMS 账号验证”列为无效用途，要求使用 SMS Retriever 等替代方案。
3. 官方明确要求：个人贷款或预算类 App 不得外传与合规功能无关的非金融或个人短信历史；隐私政策、显著披露和用户同意不能把不允许的用途变成允许用途。
4. Google Play 金融服务政策要求个人贷款 App 设置 Finance 类别、披露最短/最长还款期限、最高 APR、代表性总成本和完整隐私政策，并遵守目标国家法律。
5. 金融服务政策的通用要求明确禁止个人贷款 App 访问 `ACCESS_FINE_LOCATION`、`READ_PHONE_NUMBERS`、`QUERY_ALL_PACKAGES`、联系人、照片等敏感数据。加纳许可不能豁免这些 Play 平台限制。
6. 金融服务政策还禁止要求 60 天或更短时间内全额偿还的个人贷款；如果面向美国，APR 不得达到 36% 或以上。目标国家、产品类型与贷款条款必须逐项核验。

### 对 GalaCredit 的直接影响

- 不能在 Google Play 版本中恢复“读取并保存全部短信正文”功能。
- 不能以风控、行为分析、违约预测或用户授权作为 `READ_SMS` 的理由。
- 手机号验证应使用用户手动输入验证码或 SMS Retriever API。
- 借贷风险应改用用户主动提交的账单/交易文件、合规开放银行接口、申请表信息和服务内还款行为。
- 设备风险应使用 Play Integrity、应用安装实例随机 ID、Root/模拟器/调试环境检测等最小化信号。
- 本次安卓代码已移除短信权限和短信采集逻辑；后续 Play 版本不得重新加入。

### 许可与例外边界

加纳当地业务许可可以证明业务主体具备当地经营资格，但不能替代：

- Google Play 权限声明和逐案审批；
- Google Play Financial features declaration；
- Data safety 表单与隐私政策；
- Android/Google Play 的受限权限、敏感数据和最小权限要求。

只有当 App 的实际核心功能是政策允许的短信处理器/默认处理器，且满足对应注册、核心功能、显著披露和审核要求时，才有可能申请短信权限。GalaCredit 当前是借贷用户端，不符合该核心功能定位。
