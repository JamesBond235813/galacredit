#
转储表 admins
# ------------------------------------------------------------

CREATE TABLE `admins`
(
    `id`            INT                                                           NOT NULL AUTO_INCREMENT,
    `username`      VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  NOT NULL,
    `password_hash` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `created_at`    DATETIME DEFAULT NULL,
    `permissions`   TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `updated_at`    DATETIME DEFAULT NULL,
    `roles`         TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_admins_username` (`username`),
    KEY             `ix_admins_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 channels
# ------------------------------------------------------------

CREATE TABLE `channels`
(
    `id`           INT                                                          NOT NULL AUTO_INCREMENT,
    `channel_name` VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `sales_name`   VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `status`       VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `note`         VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `created_at`   DATETIME                                                     NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_channels_channel_name` (`channel_name`),
    KEY            `ix_channels_id` (`id`),
    KEY            `ix_channels_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 ecard_pool
# ------------------------------------------------------------

CREATE TABLE `ecard_pool`
(
    `id`          INT                                                           NOT NULL AUTO_INCREMENT,
    `account`     VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `password`    VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `face_value`  FLOAT                                                         NOT NULL,
    `expires_at`  DATETIME                                                      NOT NULL,
    `status`      VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  NOT NULL,
    `loan_id`     INT                                                           DEFAULT NULL,
    `note`        VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `assigned_at` DATETIME                                                      DEFAULT NULL,
    `created_at`  DATETIME                                                      NOT NULL,
    `updated_at`  DATETIME                                                      NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_ecard_pool_account` (`account`),
    KEY           `ix_ecard_pool_id` (`id`),
    KEY           `ix_ecard_pool_expires_at` (`expires_at`),
    KEY           `ix_ecard_pool_status` (`status`),
    KEY           `ix_ecard_pool_face_value` (`face_value`),
    KEY           `ix_ecard_pool_loan_id` (`loan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 loan_installments
# ------------------------------------------------------------

CREATE TABLE `loan_installments`
(
    `id`                           INT                                                          NOT NULL AUTO_INCREMENT,
    `loan_id`                      INT                                                          NOT NULL,
    `period_no`                    INT                                                          NOT NULL,
    `due_date`                     DATETIME                                                     NOT NULL,
    `status`                       VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `principal_amount`             FLOAT                                                        NOT NULL,
    `interest_amount`              FLOAT                                                        NOT NULL,
    `guarantee_fee_amount`         FLOAT                                                        NOT NULL,
    `due_amount`                   FLOAT                                                        NOT NULL,
    `paid_principal_amount`        FLOAT                                                        NOT NULL,
    `paid_interest_amount`         FLOAT                                                        NOT NULL,
    `paid_guarantee_fee_amount`    FLOAT                                                        NOT NULL,
    `paid_amount`                  FLOAT                                                        NOT NULL,
    `reduced_principal_amount`     FLOAT                                                        NOT NULL,
    `reduced_interest_amount`      FLOAT                                                        NOT NULL,
    `reduced_guarantee_fee_amount` FLOAT                                                        NOT NULL,
    `reduction_amount`             FLOAT                                                        NOT NULL,
    `settled_at`                   DATETIME DEFAULT NULL,
    `created_at`                   DATETIME                                                     NOT NULL,
    PRIMARY KEY (`id`),
    KEY                            `ix_loan_installments_period_no` (`period_no`),
    KEY                            `ix_loan_installments_status` (`status`),
    KEY                            `ix_loan_installments_loan_id` (`loan_id`),
    KEY                            `ix_loan_installments_id` (`id`),
    KEY                            `ix_loan_installments_due_date` (`due_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 loan_transactions
# ------------------------------------------------------------

CREATE TABLE `loan_transactions`
(
    `id`                   INT                                                          NOT NULL AUTO_INCREMENT,
    `loan_id`              INT                                                          NOT NULL,
    `user_id`              INT                                                          NOT NULL,
    `transaction_type`     VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `amount`               FLOAT                                                        NOT NULL,
    `principal_amount`     FLOAT                                                        NOT NULL,
    `interest_amount`      FLOAT                                                        NOT NULL,
    `guarantee_fee_amount` FLOAT                                                        NOT NULL,
    `penalty_amount`       FLOAT                                                        NOT NULL,
    `operator_name`        VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `note`                 VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `created_at`           DATETIME                                                     NOT NULL,
    PRIMARY KEY (`id`),
    KEY                    `ix_loan_transactions_created_at` (`created_at`),
    KEY                    `ix_loan_transactions_user_id` (`user_id`),
    KEY                    `ix_loan_transactions_loan_id` (`loan_id`),
    KEY                    `ix_loan_transactions_id` (`id`),
    KEY                    `ix_loan_transactions_transaction_type` (`transaction_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 loans
# ------------------------------------------------------------

CREATE TABLE `loans`
(
    `id`                        INT NOT NULL AUTO_INCREMENT,
    `user_id`                   INT NOT NULL,
    `status`                    VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `credit_limit`              FLOAT                                                         DEFAULT NULL,
    `term_days`                 INT                                                           DEFAULT NULL,
    `due_date`                  DATETIME                                                      DEFAULT NULL,
    `penalty_amount`            FLOAT                                                         DEFAULT NULL,
    `created_at`                DATETIME                                                      DEFAULT NULL,
    `disbursed_at`              DATETIME                                                      DEFAULT NULL,
    `review_note`               VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `approved_at`               DATETIME                                                      DEFAULT NULL,
    `reminder_count`            INT                                                           DEFAULT '0',
    `last_reminded_at`          DATETIME                                                      DEFAULT NULL,
    `collection_count`          INT                                                           DEFAULT '0',
    `last_collection_at`        DATETIME                                                      DEFAULT NULL,
    `collection_note`           VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `repaid_amount`             FLOAT                                                         DEFAULT '0',
    `reduction_amount`          FLOAT                                                         DEFAULT '0',
    `fee_rate`                  FLOAT                                                         DEFAULT '0.6',
    `fee_amount`                FLOAT                                                         DEFAULT '0',
    `paid_penalty_amount`       FLOAT                                                         DEFAULT '0',
    `reduced_penalty_amount`    FLOAT                                                         DEFAULT '0',
    `approved_credit_limit`     FLOAT                                                         DEFAULT '0',
    `product_id`                INT                                                           DEFAULT NULL,
    `product_name`              VARCHAR(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `rights_title`              VARCHAR(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `rights_desc`               VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `rights_price`              FLOAT                                                         DEFAULT '0',
    `ecard_face_value`          FLOAT                                                         DEFAULT '0',
    `product_total_price`       FLOAT                                                         DEFAULT '0',
    `product_term_days`         INT                                                           DEFAULT NULL,
    `ecard_account`             VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `ecard_password`            VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `ecard_expires_at`          DATETIME                                                      DEFAULT NULL,
    `repay_attempt_count`       INT                                                           DEFAULT '0',
    `review_admin_id`           INT                                                           DEFAULT NULL,
    `collection_admin_id`       INT                                                           DEFAULT NULL,
    `collection_transferred_at` DATETIME                                                      DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY                         `ix_loans_user_id` (`user_id`),
    KEY                         `ix_loans_id` (`id`),
    KEY                         `ix_loans_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 products
# ------------------------------------------------------------

CREATE TABLE `products`
(
    `id`               INT                                                           NOT NULL AUTO_INCREMENT,
    `name`             VARCHAR(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `ecard_face_value` FLOAT                                                         NOT NULL,
    `rights_price`     FLOAT                                                         NOT NULL,
    `rights_title`     VARCHAR(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `rights_desc`      TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `term_days`        INT                                                           NOT NULL,
    `payment_amount`   FLOAT                                                         NOT NULL,
    `is_active`        TINYINT(1) NOT NULL,
    `created_at`       DATETIME                                                      NOT NULL,
    `updated_at`       DATETIME                                                      NOT NULL,
    PRIMARY KEY (`id`),
    KEY                `ix_products_name` (`name`),
    KEY                `ix_products_is_active` (`is_active`),
    KEY                `ix_products_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 risk_control_report
# ------------------------------------------------------------

CREATE TABLE `risk_control_report`
(
    `id`          INT NOT NULL AUTO_INCREMENT,
    `name`        VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `id_card`     VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `phone`       VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `report_json` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `query_time`  DATETIME                                                      DEFAULT NULL,
    `created_at`  DATETIME                                                      DEFAULT NULL,
    `updated_at`  DATETIME                                                      DEFAULT NULL,
    `source`      VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY           `ix_risk_control_report_name` (`name`),
    KEY           `ix_risk_control_report_id` (`id`),
    KEY           `ix_risk_control_report_phone` (`phone`),
    KEY           `ix_risk_control_report_id_card` (`id_card`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 user_events
# ------------------------------------------------------------

CREATE TABLE `user_events`
(
    `id`            INT                                                           NOT NULL AUTO_INCREMENT,
    `user_id`       INT                                                           NOT NULL,
    `loan_id`       INT                                                          DEFAULT NULL,
    `actor_type`    VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  NOT NULL,
    `event_type`    VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  NOT NULL,
    `title`         VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `detail`        TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `created_at`    DATETIME                                                     DEFAULT NULL,
    `operator_name` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY             `ix_user_events_user_id` (`user_id`),
    KEY             `ix_user_events_loan_id` (`loan_id`),
    KEY             `ix_user_events_event_type` (`event_type`),
    KEY             `ix_user_events_created_at` (`created_at`),
    KEY             `ix_user_events_actor_type` (`actor_type`),
    KEY             `ix_user_events_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



#
转储表 users
# ------------------------------------------------------------

CREATE TABLE `users`
(
    `id`                          INT                                                          NOT NULL AUTO_INCREMENT,
    `phone`                       VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `name`                        VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `id_card_num`                 VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `id_address`                  VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `id_expiry`                   VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `approved_limit`              INT                                                           DEFAULT NULL,
    `created_at`                  DATETIME                                                      DEFAULT NULL,
    `emergency_contact1_name`     VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `emergency_contact1_relation` VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `emergency_contact1_phone`    VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `emergency_contact2_name`     VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `emergency_contact2_relation` VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `emergency_contact2_phone`    VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `face_auth_status`            VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT 'PENDING',
    `face_auth_at`                DATETIME                                                      DEFAULT NULL,
    `last_login_at`               DATETIME                                                      DEFAULT NULL,
    `ocr_submitted_at`            DATETIME                                                      DEFAULT NULL,
    `application_submitted_at`    DATETIME                                                      DEFAULT NULL,
    `source_channel_id`           INT                                                           DEFAULT NULL,
    `channel_bound_at`            DATETIME                                                      DEFAULT NULL,
    `last_channel_visit_at`       DATETIME                                                      DEFAULT NULL,
    `location_latitude`           VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_longitude`          VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_accuracy`           VARCHAR(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_address`            VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `location_province`           VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_city`               VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_district`           VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_street`             VARCHAR(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_source`             VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci  DEFAULT NULL,
    `location_updated_at`         DATETIME                                                      DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_users_phone` (`phone`),
    UNIQUE KEY `id_card_num` (`id_card_num`),
    KEY                           `ix_users_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


#
转储表 oauth_clients
# ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `oauth_clients`
(
    `id`             BIGINT                                                       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `client_id`      VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客户端唯一标识',
    `client_name`    VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端名称',
    `client_secret`  VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端密钥（预留）',
    `grant_types`    VARCHAR(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'sms_code,refresh_token' COMMENT '授权模式列表',
    `is_active`      TINYINT(1)                                                   NOT NULL DEFAULT '1' COMMENT '是否启用',
    `created_at`     DATETIME                                                     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME                                                     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_oauth_clients_client_id` (`client_id`),
    KEY              `idx_oauth_clients_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OAuth客户端配置表';


#
转储表 oauth_tokens
# ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `oauth_tokens`
(
    `id`                BIGINT                                                       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id`           INT                                                          NOT NULL COMMENT '用户ID',
    `phone`             VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '手机号快照',
    `client_id`         VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客户端标识',
    `access_token`      VARCHAR(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '访问令牌',
    `refresh_token`     VARCHAR(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '刷新令牌',
    `access_jti`        VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '访问令牌唯一ID',
    `refresh_jti`       VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '刷新令牌唯一ID',
    `access_expires_at` DATETIME                                                     NOT NULL COMMENT '访问令牌过期时间',
    `refresh_expires_at` DATETIME                                                    NOT NULL COMMENT '刷新令牌过期时间',
    `revoked_at`        DATETIME                                                     DEFAULT NULL COMMENT '吊销时间',
    `created_at`        DATETIME                                                     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME                                                     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_oauth_tokens_access_jti` (`access_jti`),
    UNIQUE KEY `uk_oauth_tokens_refresh_jti` (`refresh_jti`),
    KEY                 `idx_oauth_tokens_user_id` (`user_id`),
    KEY                 `idx_oauth_tokens_phone` (`phone`),
    KEY                 `idx_oauth_tokens_client_id` (`client_id`),
    KEY                 `idx_oauth_tokens_revoked_at` (`revoked_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户OAuth令牌持久化表';
