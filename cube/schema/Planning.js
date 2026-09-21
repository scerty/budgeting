cube(`Planning`, {
  sql_table: `analytics.fact_planning`,

  measures: {
    plannedAmount: {
      sql: `amount`,
      type: `sum`
    },

    planningFactCount: {
      type: `count`
    }
  },

  dimensions: {
    planningFactId: {
      sql: `planning_fact_id`,
      type: `number`,
      primaryKey: true
    },

    organizationId: {
      sql: `organization_id`,
      type: `number`
    },

    organizationCode: {
      sql: `organization_code`,
      type: `string`
    },

    organizationName: {
      sql: `organization_name`,
      type: `string`
    },

    calculationRunId: {
      sql: `calculation_run_id`,
      type: `number`
    },

    scenarioVersionId: {
      sql: `scenario_version_id`,
      type: `number`
    },

    scenarioCode: {
      sql: `scenario_code`,
      type: `string`
    },

    scenarioName: {
      sql: `scenario_name`,
      type: `string`
    },

    scenarioVersionCode: {
      sql: `scenario_version_code`,
      type: `string`
    },

    scenarioVersionName: {
      sql: `scenario_version_name`,
      type: `string`
    },

    scenarioVersionStatus: {
      sql: `scenario_version_status`,
      type: `string`
    },

    fiscalPeriodId: {
      sql: `fiscal_period_id`,
      type: `number`
    },

    fiscalPeriodCode: {
      sql: `fiscal_period_code`,
      type: `string`
    },

    fiscalPeriodName: {
      sql: `fiscal_period_name`,
      type: `string`
    },

    fiscalYear: {
      sql: `fiscal_year`,
      type: `number`
    },

    legalEntityId: {
      sql: `legal_entity_id`,
      type: `number`
    },

    legalEntityCode: {
      sql: `legal_entity_code`,
      type: `string`
    },

    legalEntityName: {
      sql: `legal_entity_name`,
      type: `string`
    },

    groupAccountId: {
      sql: `group_account_id`,
      type: `number`
    },

    groupAccountCode: {
      sql: `group_account_code`,
      type: `string`
    },

    groupAccountName: {
      sql: `group_account_name`,
      type: `string`
    },

    entityAccountId: {
      sql: `entity_account_id`,
      type: `number`
    },

    branchId: {
      sql: `branch_id`,
      type: `number`
    },

    branchCode: {
      sql: `branch_code`,
      type: `string`
    },

    branchName: {
      sql: `branch_name`,
      type: `string`
    },

    departmentId: {
      sql: `department_id`,
      type: `number`
    },

    departmentCode: {
      sql: `department_code`,
      type: `string`
    },

    departmentName: {
      sql: `department_name`,
      type: `string`
    },

    sourceKind: {
      sql: `source_kind`,
      type: `string`
    },

    currencyCode: {
      sql: `currency_code`,
      type: `string`
    },

    calculationRunStatus: {
      sql: `calculation_run_status`,
      type: `string`
    }
  }
});