cube(`JournalLines`, {
  sql_table: `analytics.fact_journal_lines`,

  measures: {
    debitAmount: {
      sql: `debit_amount`,
      type: `sum`
    },

    creditAmount: {
      sql: `credit_amount`,
      type: `sum`
    },

    signedAmount: {
      sql: `signed_amount`,
      type: `sum`
    },

    journalLineCount: {
      type: `count`
    }
  },

  dimensions: {
    journalLineId: {
      sql: `journal_line_id`,
      type: `number`,
      primaryKey: true
    },

    documentNumber: {
      sql: `document_number`,
      type: `string`
    },

    lineNumber: {
      sql: `line_number`,
      type: `number`
    },

    postingDate: {
      sql: `posting_date`,
      type: `time`
    },

    sourceAccountCode: {
      sql: `source_account_code`,
      type: `string`
    },

    sourceLegalEntityCode: {
      sql: `source_legal_entity_code`,
      type: `string`
    },

    currencyCode: {
      sql: `currency_code`,
      type: `string`
    },

    reportingCurrencyCode: {
      sql: `reporting_currency_code`,
      type: `string`
    },

    sourceSystem: {
      sql: `source_system`,
      type: `string`
    }
  }
});