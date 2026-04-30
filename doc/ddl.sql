
# 转储表 admins
# ------------------------------------------------------------

DROP TABLE IF EXISTS `admins`;

CREATE TABLE `admins` (
                          `id` int NOT NULL AUTO_INCREMENT,
                          `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                          `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                          `created_at` datetime DEFAULT NULL,
                          `permissions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                          `updated_at` datetime DEFAULT NULL,
                          `roles` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                          PRIMARY KEY (`id`),
                          UNIQUE KEY `ix_admins_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 channels
# ------------------------------------------------------------

DROP TABLE IF EXISTS `channels`;

CREATE TABLE `channels` (
                            `id` int NOT NULL AUTO_INCREMENT,
                            `channel_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                            `sales_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                            `admin_user_id` int DEFAULT '0',
                            `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                            `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                            `created_at` datetime NOT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE KEY `ix_channels_channel_name` (`channel_name`),
                            KEY `ix_channels_id` (`id`),
                            KEY `ix_channels_status` (`status`),
                            KEY `ix_channels_admin_user_id` (`admin_user_id`),
                            KEY `idx_admuid_id` (`admin_user_id`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 ecard_pool
# ------------------------------------------------------------

DROP TABLE IF EXISTS `ecard_pool`;

CREATE TABLE `ecard_pool` (
                              `id` int NOT NULL AUTO_INCREMENT,
                              `account` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                              `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                              `face_value` float NOT NULL,
                              `expires_at` datetime NOT NULL,
                              `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                              `loan_id` int DEFAULT NULL,
                              `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                              `assigned_at` datetime DEFAULT NULL,
                              `created_at` datetime NOT NULL,
                              `updated_at` datetime NOT NULL,
                              PRIMARY KEY (`id`),
                              UNIQUE KEY `ix_ecard_pool_account` (`account`),
                              KEY `ix_ecard_pool_id` (`id`),
                              KEY `ix_ecard_pool_expires_at` (`expires_at`),
                              KEY `ix_ecard_pool_status` (`status`),
                              KEY `ix_ecard_pool_face_value` (`face_value`),
                              KEY `ix_ecard_pool_loan_id` (`loan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 loan_installments
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loan_installments`;

CREATE TABLE `loan_installments` (
                                     `id` int NOT NULL AUTO_INCREMENT,
                                     `loan_id` int NOT NULL,
                                     `period_no` int NOT NULL,
                                     `due_date` datetime NOT NULL,
                                     `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                                     `principal_amount` float NOT NULL,
                                     `interest_amount` float NOT NULL,
                                     `guarantee_fee_amount` float NOT NULL,
                                     `due_amount` float NOT NULL,
                                     `paid_principal_amount` float NOT NULL,
                                     `paid_interest_amount` float NOT NULL,
                                     `paid_guarantee_fee_amount` float NOT NULL,
                                     `paid_amount` float NOT NULL,
                                     `reduced_principal_amount` float NOT NULL,
                                     `reduced_interest_amount` float NOT NULL,
                                     `reduced_guarantee_fee_amount` float NOT NULL,
                                     `reduction_amount` float NOT NULL,
                                     `settled_at` datetime DEFAULT NULL,
                                     `created_at` datetime NOT NULL,
                                     PRIMARY KEY (`id`),
                                     KEY `ix_loan_installments_period_no` (`period_no`),
                                     KEY `ix_loan_installments_status` (`status`),
                                     KEY `ix_loan_installments_loan_id` (`loan_id`),
                                     KEY `ix_loan_installments_id` (`id`),
                                     KEY `ix_loan_installments_due_date` (`due_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 loan_transactions
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loan_transactions`;

CREATE TABLE `loan_transactions` (
                                     `id` int NOT NULL AUTO_INCREMENT,
                                     `loan_id` int NOT NULL,
                                     `user_id` int NOT NULL,
                                     `transaction_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                                     `amount` float NOT NULL,
                                     `principal_amount` float NOT NULL,
                                     `interest_amount` float NOT NULL,
                                     `guarantee_fee_amount` float NOT NULL,
                                     `penalty_amount` float NOT NULL,
                                     `operator_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                                     `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                                     `created_at` datetime NOT NULL,
                                     PRIMARY KEY (`id`),
                                     KEY `ix_loan_transactions_created_at` (`created_at`),
                                     KEY `ix_loan_transactions_user_id` (`user_id`),
                                     KEY `ix_loan_transactions_loan_id` (`loan_id`),
                                     KEY `ix_loan_transactions_id` (`id`),
                                     KEY `ix_loan_transactions_transaction_type` (`transaction_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 loans
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loans`;

CREATE TABLE `loans` (
                         `id` int NOT NULL AUTO_INCREMENT,
                         `user_id` int NOT NULL,
                         `order_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '订单号',
                         `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `credit_limit` float DEFAULT NULL,
                         `term_days` int DEFAULT NULL,
                         `due_date` datetime DEFAULT NULL,
                         `penalty_amount` float DEFAULT NULL,
                         `created_at` datetime DEFAULT NULL,
                         `disbursed_at` datetime DEFAULT NULL,
                         `review_note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `approved_at` datetime DEFAULT NULL,
                         `reminder_count` int DEFAULT '0',
                         `last_reminded_at` datetime DEFAULT NULL,
                         `collection_count` int DEFAULT '0',
                         `last_collection_at` datetime DEFAULT NULL,
                         `collection_note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `repaid_amount` float DEFAULT '0',
                         `reduction_amount` float DEFAULT '0',
                         `fee_rate` float DEFAULT '0.6',
                         `fee_amount` float DEFAULT '0',
                         `paid_penalty_amount` float DEFAULT '0',
                         `reduced_penalty_amount` float DEFAULT '0',
                         `approved_credit_limit` float DEFAULT '0',
                         `product_id` int DEFAULT NULL,
                         `product_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `rights_title` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `rights_desc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `rights_price` float DEFAULT '0',
                         `ecard_face_value` float DEFAULT '0',
                         `product_total_price` float DEFAULT '0',
                         `product_term_days` int DEFAULT NULL,
                         `ecard_account` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `ecard_password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `ecard_expires_at` datetime DEFAULT NULL,
                         `repay_attempt_count` int DEFAULT '0',
                         `review_admin_id` int DEFAULT NULL,
                         `collection_admin_id` int DEFAULT NULL,
                         `collection_transferred_at` datetime DEFAULT NULL,
                         PRIMARY KEY (`id`),
                         KEY `ix_loans_user_id` (`user_id`),
                         KEY `ix_loans_id` (`id`),
                         KEY `ix_loans_status` (`status`),
                         KEY `idx_order_no` (`order_no`),
                         KEY `idx_usr_disburse` (`user_id`,`disbursed_at`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 oauth_clients
# ------------------------------------------------------------

DROP TABLE IF EXISTS `oauth_clients`;

CREATE TABLE `oauth_clients` (
                                 `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                                 `client_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客户端唯一标识',
                                 `client_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端名称',
                                 `client_secret` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端密钥（预留）',
                                 `grant_types` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'sms_code,refresh_token' COMMENT '授权模式列表',
                                 `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
                                 `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                 `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                                 PRIMARY KEY (`id`),
                                 UNIQUE KEY `uk_oauth_clients_client_id` (`client_id`),
                                 KEY `idx_oauth_clients_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OAuth客户端配置表';



# 转储表 oauth_tokens
# ------------------------------------------------------------

DROP TABLE IF EXISTS `oauth_tokens`;

CREATE TABLE `oauth_tokens` (
                                `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                                `user_id` int NOT NULL COMMENT '用户ID',
                                `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '手机号快照',
                                `client_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客户端标识',
                                `access_token` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '访问令牌',
                                `refresh_token` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '刷新令牌',
                                `access_jti` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '访问令牌唯一ID',
                                `refresh_jti` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '刷新令牌唯一ID',
                                `access_expires_at` datetime NOT NULL COMMENT '访问令牌过期时间',
                                `refresh_expires_at` datetime NOT NULL COMMENT '刷新令牌过期时间',
                                `revoked_at` datetime DEFAULT NULL COMMENT '吊销时间',
                                `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                                PRIMARY KEY (`id`),
                                UNIQUE KEY `uk_oauth_tokens_access_jti` (`access_jti`),
                                UNIQUE KEY `uk_oauth_tokens_refresh_jti` (`refresh_jti`),
                                KEY `idx_oauth_tokens_user_id` (`user_id`),
                                KEY `idx_oauth_tokens_phone` (`phone`),
                                KEY `idx_oauth_tokens_client_id` (`client_id`),
                                KEY `idx_oauth_tokens_revoked_at` (`revoked_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户OAuth令牌持久化表';



# 转储表 products
# ------------------------------------------------------------

DROP TABLE IF EXISTS `products`;

CREATE TABLE `products` (
                            `id` int NOT NULL AUTO_INCREMENT,
                            `name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                            `ecard_face_value` float NOT NULL,
                            `rights_price` float NOT NULL,
                            `rights_title` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                            `rights_desc` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                            `term_days` int NOT NULL,
                            `payment_amount` float NOT NULL,
                            `is_active` tinyint(1) NOT NULL,
                            `created_at` datetime NOT NULL,
                            `updated_at` datetime NOT NULL,
                            PRIMARY KEY (`id`),
                            KEY `ix_products_name` (`name`),
                            KEY `ix_products_is_active` (`is_active`),
                            KEY `ix_products_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 risk_control_report
# ------------------------------------------------------------

DROP TABLE IF EXISTS `risk_control_report`;

CREATE TABLE `risk_control_report` (
                                       `id` int NOT NULL AUTO_INCREMENT,
                                       `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                                       `id_card` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                                       `phone` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                                       `report_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                                       `query_time` datetime DEFAULT NULL,
                                       `created_at` datetime DEFAULT NULL,
                                       `updated_at` datetime DEFAULT NULL,
                                       `source` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                                       PRIMARY KEY (`id`),
                                       KEY `ix_risk_control_report_name` (`name`),
                                       KEY `ix_risk_control_report_id` (`id`),
                                       KEY `ix_risk_control_report_phone` (`phone`),
                                       KEY `ix_risk_control_report_id_card` (`id_card`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 user_events
# ------------------------------------------------------------

DROP TABLE IF EXISTS `user_events`;

CREATE TABLE `user_events` (
                               `id` int NOT NULL AUTO_INCREMENT,
                               `user_id` int NOT NULL,
                               `loan_id` int DEFAULT NULL,
                               `actor_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                               `event_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                               `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                               `detail` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                               `created_at` datetime DEFAULT NULL,
                               `operator_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                               PRIMARY KEY (`id`),
                               KEY `ix_user_events_user_id` (`user_id`),
                               KEY `ix_user_events_loan_id` (`loan_id`),
                               KEY `ix_user_events_event_type` (`event_type`),
                               KEY `ix_user_events_created_at` (`created_at`),
                               KEY `ix_user_events_actor_type` (`actor_type`),
                               KEY `ix_user_events_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



# 转储表 users
# ------------------------------------------------------------

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
                         `id` int NOT NULL AUTO_INCREMENT,
                         `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                         `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登录密码哈希',
                         `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `id_card_num` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `id_address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `id_expiry` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `approved_limit` int DEFAULT NULL,
                         `created_at` datetime DEFAULT NULL,
                         `emergency_contact1_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `emergency_contact1_relation` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `emergency_contact1_phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `emergency_contact2_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `emergency_contact2_relation` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `emergency_contact2_phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `face_auth_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'PENDING',
                         `real_name_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'UNVERIFIED',
                         `face_auth_at` datetime DEFAULT NULL,
                         `last_login_at` datetime DEFAULT NULL,
                         `ocr_submitted_at` datetime DEFAULT NULL,
                         `application_submitted_at` datetime DEFAULT NULL,
                         `source_channel_id` int DEFAULT NULL,
                         `channel_bound_at` datetime DEFAULT NULL,
                         `last_channel_visit_at` datetime DEFAULT NULL,
                         `location_latitude` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_longitude` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_accuracy` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_district` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_street` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_source` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
                         `location_updated_at` datetime DEFAULT NULL,
                         PRIMARY KEY (`id`),
                         UNIQUE KEY `ix_users_phone` (`phone`),
                         UNIQUE KEY `id_card_num` (`id_card_num`),
                         KEY `idx_ch_created` (`source_channel_id`,`created_at`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


