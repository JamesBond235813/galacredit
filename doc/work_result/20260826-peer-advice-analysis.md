# 2026-08-26 21:20:00

## 对同行短信抓取建议的政策分析

### 截图内容

同行建议的原意是：可以抓取短信，但应按业务目标筛选，例如贷款 App 只抓取贷款类别的信息。

### 分析结论

- “只抓贷款相关短信”符合数据最小化和目的限定原则，但不是 Google Play 自动批准短信权限的规则。
- Google Play 的 SMS 权限政策按 App 的核心功能和允许用途审查，不仅按关键词过滤范围审查。
- “贷款风险评估/用户行为分析”并未因为只筛选 loan、repayment、overdue 等关键词，就自动成为允许的 SMS 权限用途。
- Google Play 官方明确禁止个人贷款/预算类 App 外传与合规功能无关的非金融或个人短信；这并不等同于允许贷款 App 任意读取金融短信。
- 如果主张“SMS-based financial transactions”或“SMS-based money management”例外，必须证明短信处理是 App 的核心功能、没有更安全替代方案，并提交 Permissions Declaration Form，接受逐案审批。GalaCredit 当前核心功能是借贷申请和风控，不是短信金融交易管理器，因此不能预设会获批。
- 加纳业务许可、用户同意、关键词筛选和只上传摘要，都不能替代 Play 权限审批、金融服务声明和 User Data Policy 要求。

### 对 GalaCredit 的建议

1. Google Play 版本：不申请 `READ_SMS`，使用 SMS Retriever 完成验证码；贷款风险改用开放银行/账单上传/服务内还款行为/Play Integrity 等信号。
2. 非 Play 版本：如果确有法律和业务必要，可以另行评估用户主动选择的金融短信导入，但需单独完成法律依据、显著披露、可撤回授权、加密、保存期限、删除机制和访问审计；不能把该版本作为规避 Play 审核的方式。
3. 若坚持为 Play 版本申请短信权限，应先向 Google Play 提交正式权限声明，说明核心功能、具体权限、处理范围、替代方案评估、数据流向和演示账号；在获得书面批准前，不应发布含该权限的 APK。

### 参考政策

- https://support.google.com/googleplay/android-developer/answer/10208820
- https://support.google.com/googleplay/android-developer/answer/9876821
- https://support.google.com/googleplay/android-developer/answer/10144311
