cube(`ExpensesByBranch`, {
  sql_table: `analytics.expenses_by_branch`,

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
    branchId: {
      sql: `branch_id`,
      type: `number`,
      primaryKey: true
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
    }
  }
});
