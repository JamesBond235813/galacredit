import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));
const monitoringSource = readFileSync(resolve(currentDir, 'Monitoring.vue'), 'utf-8');
const auditLogSource = readFileSync(resolve(currentDir, 'AuditLog.vue'), 'utf-8');
const kycReviewSource = readFileSync(resolve(currentDir, 'KycReview.vue'), 'utf-8');
const messageCenterSource = readFileSync(resolve(currentDir, 'MessageCenter.vue'), 'utf-8');
const riskStrategySource = readFileSync(resolve(currentDir, 'RiskStrategy.vue'), 'utf-8');
const contentConfigSource = readFileSync(resolve(currentDir, 'ContentConfig.vue'), 'utf-8');

describe('ops center pages', () => {
  it('should bind monitoring to scheduler summary data', () => {
    expect(monitoringSource).toContain('getMonitoringSummary');
    expect(monitoringSource).toContain('scheduled_jobs');
  });

  it('should expose audit, kyc and message center data tables', () => {
    expect(auditLogSource).toContain('getAdminAuditLogs');
    expect(kycReviewSource).toContain('getKycReviewQueue');
    expect(messageCenterSource).toContain('getMessageCenter');
    expect(messageCenterSource).toContain('sendAdminReminder');
  });

  it('should expose shadow risk decision records and filters', () => {
    expect(riskStrategySource).toContain('getRiskDecisions');
    expect(riskStrategySource).toContain('shadow mode');
    expect(riskStrategySource).toContain('rule_hits');
  });

  it('should persist ops content drafts locally for now', () => {
    expect(contentConfigSource).toContain('galacredit_content_config_draft');
    expect(contentConfigSource).toContain('首页公告');
    expect(contentConfigSource).toContain('Banner');
    expect(contentConfigSource).toContain('FAQ');
  });
});
