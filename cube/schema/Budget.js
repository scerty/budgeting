cube(`Budget`, {
  sql_table: `analytics.fact_budget`,

  measures: {
    totalBudget: {
      sql: `amount`,
      type: `sum`
    },

    budgetLineCount: {
      type: `count`
    }
  },

  dimensions: {
    budgetLineId: {
      sql: `budget_line_id`,
      type: `number`,
      primaryKey: true
    },

    organizationId: {
      sql: `organization_id`,
      type: `number`
    },

    budgetVersionId: {
      sql: `budget_version_id`,
      type: `number`
    },

    budgetVersionCode: {
      sql: `budget_version_code`,
      type: `string`
    },

    budgetStatus: {
      sql: `budget_status`,
      type: `string`
    },

    scenario: {
      sql: `scenario`,
      type: `string`
    },

    fiscalPeriodId: {
      sql: `fiscal_period_id`,
      type: `number`
    },

    legalEntityId: {
      sql: `legal_entity_id`,
      type: `number`
    },

    groupAccountId: {
      sql: `group_account_id`,
      type: `number`
    },

    entityAccountId: {
      sql: `entity_account_id`,
      type: `number`
    },

    branchId: {
      sql: `branch_id`,
      type: `number`
    },

    departmentId: {
      sql: `department_id`,
      type: `number`
    },

    currencyCode: {
      sql: `currency_code`,
      type: `string`
    }
  }
});