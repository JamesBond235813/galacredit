-- 后台账号启停能力
ALTER TABLE admins ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用';

CREATE TABLE admin_login_histories (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '登录历史ID', admin_id INT NOT NULL COMMENT '管理员ID',
  username VARCHAR(50) NOT NULL COMMENT '登录用户名', client_type VARCHAR(20) NOT NULL DEFAULT 'WEB' COMMENT '客户端类型',
  ip VARCHAR(64) NULL COMMENT '登录IP', user_agent VARCHAR(500) NULL COMMENT '客户端标识', success TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否成功',
  failure_reason VARCHAR(255) NULL COMMENT '失败原因', created_at DATETIME NOT NULL COMMENT '登录时间', INDEX idx_admin_login_admin_time(admin_id, created_at)
) COMMENT='后台登录历史';
CREATE TABLE config_change_histories (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '变更历史ID', object_type VARCHAR(20) NOT NULL COMMENT '对象类型', object_id INT NOT NULL COMMENT '对象ID',
  action VARCHAR(20) NOT NULL COMMENT '变更动作', version_no INT NOT NULL DEFAULT 1 COMMENT '版本号', snapshot_json TEXT NOT NULL COMMENT '配置快照',
  operator_name VARCHAR(50) NULL COMMENT '操作人', created_at DATETIME NOT NULL COMMENT '变更时间', INDEX idx_config_history_object(object_type, object_id, created_at)
) COMMENT='渠道产品配置变更历史';
CREATE TABLE message_templates (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID', template_key VARCHAR(80) NOT NULL COMMENT '模板标识', version_no INT NOT NULL DEFAULT 1 COMMENT '模板版本',
  title VARCHAR(120) NOT NULL COMMENT '模板标题', content TEXT NOT NULL COMMENT '模板内容', is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  created_by VARCHAR(50) NULL COMMENT '创建人', created_at DATETIME NOT NULL COMMENT '创建时间', INDEX idx_message_template_key(template_key, version_no)
) COMMENT='消息模板';
