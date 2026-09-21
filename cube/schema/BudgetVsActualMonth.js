cube(`BudgetVsActualMonth`, {
  sql_table: `analytics.budget_vs_actual_month`,

  measures: {
    budgetAmount: {
      sql: `budget_amount`,
      type: `sum`
    },

    actualAmount: {
      sql: `actual_amount`,
      type: `sum`
    },

    varianceAmount: {
      sql: `variance_amount`,
      type: `sum`
    }
  },

  dimensions: {
    organizationCode: {
      sql: `organization_code`,
      type: `string`
    },

    organizationName: {
      sql: `organization_name`,
      type: `string`
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

    monthKey: {
      sql: `month_key`,
      type: `number`
    },

    monthYear: {
      sql: `month_year`,
      type: `number`
    },

    monthName: {
      sql: `month_name`,
      type: `string`
    },

    groupAccountCode: {
      sql: `group_account_code`,
      type: `string`
    },

    groupAccountName: {
      sql: `group_account_name`,
      type: `string`
    },

    legalEntityCode: {
      sql: `legal_entity_code`,
      type: `string`
    },

    legalEntityName: {
      sql: `legal_entity_name`,
      type: `string`
    },

    branchCode: {
      sql: `branch_code`,
      type: `string`
    },

    branchName: {
      sql: `branch_name`,
      type: `string`
    },

    departmentCode: {
      sql: `department_code`,
      type: `string`
    },

    departmentName: {
      sql: `department_name`,
      type: `string`
    },

    currencyCode: {
      sql: `currency_code`,
      type: `string`
    }
  }
});