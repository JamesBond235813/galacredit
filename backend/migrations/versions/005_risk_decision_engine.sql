CREATE TABLE risk_policy_versions (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '策略版本ID',
  policy_key VARCHAR(80) NOT NULL COMMENT '策略标识',
  version_no INT NOT NULL COMMENT '策略版本号',
  status VARCHAR(20) NOT NULL DEFAULT 'SHADOW' COMMENT '策略状态',
  config_json TEXT NOT NULL COMMENT '策略配置JSON',
  rollout_percent INT NOT NULL DEFAULT 0 COMMENT '灰度比例百分比',
  created_by VARCHAR(50) NULL COMMENT '创建人',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  INDEX idx_risk_policy_key_status(policy_key, status, version_no)
) COMMENT='风控策略版本';

CREATE TABLE risk_decisions (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '决策ID',
  decision_id VARCHAR(40) NOT NULL UNIQUE COMMENT '决策流水号',
  user_id INT NOT NULL COMMENT '用户ID',
  loan_id INT NULL COMMENT '订单ID',
  stage VARCHAR(30) NOT NULL COMMENT '决策阶段',
  decision VARCHAR(20) NOT NULL COMMENT '决策结果',
  score DECIMAL(8,2) NULL COMMENT '综合风险分',
  policy_key VARCHAR(80) NOT NULL COMMENT '策略标识',
  policy_version VARCHAR(30) NOT NULL COMMENT '策略版本',
  mode VARCHAR(20) NOT NULL DEFAULT 'SHADOW' COMMENT '执行模式',
  reason_codes_json TEXT NOT NULL COMMENT '标准原因码JSON数组',
  feature_snapshot_json TEXT NOT NULL COMMENT '特征快照JSON',
  created_at DATETIME NOT NULL COMMENT '决策时间',
  INDEX idx_risk_decision_user_stage(user_id, stage, created_at),
  INDEX idx_risk_decision_loan_stage(loan_id, stage, created_at)
) COMMENT='风控决策记录';

CREATE TABLE risk_rule_hits (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '规则命中ID',
  decision_id VARCHAR(40) NOT NULL COMMENT '决策流水号',
  rule_code VARCHAR(80) NOT NULL COMMENT '规则编码',
  outcome VARCHAR(20) NOT NULL COMMENT '规则结果',
  severity VARCHAR(20) NOT NULL DEFAULT 'INFO' COMMENT '严重级别',
  detail VARCHAR(500) NULL COMMENT '规则命中说明',
  created_at DATETIME NOT NULL COMMENT '命中时间',
  INDEX idx_risk_rule_hit_decision(decision_id),
  INDEX idx_risk_rule_hit_code(rule_code, created_at)
) COMMENT='风控规则命中记录';

INSERT INTO risk_policy_versions(policy_key, version_no, status, config_json, rollout_percent, created_by, created_at)
SELECT 'GHANA_CASH_LOAN_BASELINE', 1, 'SHADOW', '{"mode":"SHADOW","description":"Ghana cash-loan baseline rules"}', 0, 'SYSTEM', NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM risk_policy_versions WHERE policy_key = 'GHANA_CASH_LOAN_BASELINE' AND version_no = 1
);
