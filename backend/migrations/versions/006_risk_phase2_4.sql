CREATE TABLE IF NOT EXISTS risk_manual_overrides (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '人工覆盖ID',
  decision_id VARCHAR(40) NOT NULL COMMENT '决策流水号', action VARCHAR(20) NOT NULL COMMENT '覆盖动作',
  reason VARCHAR(500) NOT NULL COMMENT '覆盖原因', operator_id INT NOT NULL COMMENT '操作者ID',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间', INDEX idx_rmo_decision (decision_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风控人工覆盖记录';
CREATE TABLE IF NOT EXISTS risk_device_signals (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '特征记录ID', user_id INT NOT NULL COMMENT '用户ID',
  device_fingerprint VARCHAR(128) NULL COMMENT '设备指纹', ip_address VARCHAR(64) NULL COMMENT 'IP地址',
  asn VARCHAR(64) NULL COMMENT '网络ASN', is_proxy TINYINT NOT NULL DEFAULT 0 COMMENT '是否代理网络',
  is_emulator TINYINT NOT NULL DEFAULT 0 COMMENT '是否模拟器', application_count_24h INT NOT NULL DEFAULT 0 COMMENT '24小时申请次数',
  account_count_24h INT NOT NULL DEFAULT 0 COMMENT '24小时关联账户数', payload_json TEXT NOT NULL COMMENT '原始特征JSON',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间', INDEX idx_rds_user (user_id), INDEX idx_rds_device (device_fingerprint)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备和速度特征';
CREATE TABLE IF NOT EXISTS risk_external_checks (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '查询记录ID', user_id INT NOT NULL COMMENT '用户ID', provider VARCHAR(80) NOT NULL COMMENT '供应商标识',
  check_type VARCHAR(40) NOT NULL COMMENT '查询类型', status VARCHAR(20) NOT NULL COMMENT '查询状态', score DECIMAL(8,2) NULL COMMENT '外部评分',
  reason VARCHAR(500) NULL COMMENT '结果说明', response_json TEXT NOT NULL COMMENT '脱敏响应JSON', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '查询时间', INDEX idx_rec_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部数据查询记录';
CREATE TABLE IF NOT EXISTS risk_model_scores (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模型评分ID', decision_id VARCHAR(40) NOT NULL COMMENT '决策流水号', model_key VARCHAR(80) NOT NULL COMMENT '模型标识',
  model_version VARCHAR(40) NOT NULL COMMENT '模型版本', score DECIMAL(8,4) NOT NULL COMMENT '模型评分', mode VARCHAR(20) NOT NULL DEFAULT 'SHADOW' COMMENT '执行模式',
  explanation_json TEXT NOT NULL COMMENT '解释因子JSON', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评分时间', INDEX idx_rms_decision (decision_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型评分记录';
