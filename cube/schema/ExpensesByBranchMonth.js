cube(`ExpensesByBranchMonth`, {
  sql_table: `analytics.expenses_by_branch_month`,

  measures: {
    totalExpenses: {
      sql: `total_expenses`,
      type: `sum`
    },

    expenseCount: {
      sql: `expense_count`,
      type: `sum`
    }
  },

  dimensions: {
    branchMonthKey: {
      sql: `concat(branch_id, '_', month_key)`,
      type: `string`,
      primaryKey: true
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

    city: {
      sql: `city`,
      type: `string`
    },

    monthKey: {
      sql: `month_key`,
      type: `number`
    },

    year: {
      sql: `year`,
      type: `number`
    },

    monthNumber: {
      sql: `month_number`,
      type: `number`
    },

    monthName: {
      sql: `month_name`,
      type: `string`
    }
  }
});
