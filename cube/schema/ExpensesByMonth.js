cube(`ExpensesByMonth`, {
  sql_table: `analytics.expenses_by_month`,

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
    monthKey: {
      sql: `month_key`,
      type: `number`,
      primaryKey: true
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
