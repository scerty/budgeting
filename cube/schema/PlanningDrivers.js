cube(`PlanningDrivers`, {
  sql_table: `analytics.fact_planning_driver_values`,

  measures: {
    driverValue: {
      sql: `value`,
      type: `sum`
    },

    driverValueCount: {
      type: `count`
    }
  },

  dimensions: {
    driverValueId: {
      sql: `driver_value_id`,
      type: `number`,
      primaryKey: true
    },

    planningDriverId: {
      sql: `planning_driver_id`,
      type: `number`
    },

    organizationId: {
      sql: `organization_id`,
      type: `number`
    },

    scenarioVersionId: {
      sql: `scenario_version_id`,
      type: `number`
    },

    fiscalPeriodId: {
      sql: `fiscal_period_id`,
      type: `number`
    },

    legalEntityId: {
      sql: `legal_entity_id`,
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

    projectId: {
      sql: `project_id`,
      type: `number`
    },

    source: {
      sql: `source`,
      type: `string`
    },

    currencyId: {
      sql: `currency_id`,
      type: `number`
    }
  }
});