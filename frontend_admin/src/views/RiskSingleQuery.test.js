import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const currentDir = dirname(fileURLToPath(import.meta.url));
const pageSource = readFileSync(resolve(currentDir, 'RiskSingleQuery.vue'), 'utf-8');
const routerSource = readFileSync(resolve(currentDir, '../router/index.js'), 'utf-8');
const apiSource = readFileSync(resolve(currentDir, '../api/index.js'), 'utf-8');
const permissionSource = readFileSync(resolve(currentDir, '../constants/adminPages.js'), 'utf-8');

describe('risk single query page', () => {
  it('should provide optional identity inputs and reuse risk report dialog', () => {
    expect(pageSource).toContain('风控报告单查');
    expect(pageSource).toContain('queryForm.name');
    expect(pageSource).toContain('queryForm.id_card');
    expect(pageSource).toContain('queryForm.phone');
    expect(pageSource).toContain('查看报告');
    expect(pageSource).toContain('RiskReportDialog');
  });

  it('should list query history with report action', () => {
    expect(pageSource).toContain('查询历史清单');
    expect(pageSource).toContain('historyRows');
    expect(pageSource).toContain('openHistoryReport');
    expect(pageSource).toContain('getSingleRiskReportDetail');
  });

  it('should register route, permission and api methods', () => {
    expect(routerSource).toContain("path: 'risk-single-query'");
    expect(routerSource).toContain("permission: 'risk-single-query'");
    expect(permissionSource).toContain("key: 'risk-single-query'");
    expect(apiSource).toContain('querySingleRiskReport');
    expect(apiSource).toContain('getSingleRiskReportHistory');
    expect(apiSource).toContain('getSingleRiskReportDetail');
  });
});
