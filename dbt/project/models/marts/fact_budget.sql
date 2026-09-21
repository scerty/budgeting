{{ config(materialized='table') }}

select
    budget_line_id,
    budget_version_id,
    budget_plan_id,
    organization_id,
    fiscal_calendar_id,
    budget_version_code,
    version_type,
    scenario,
    scenario_version_id,
    budget_status,
    legal_entity_id,
    fiscal_period_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id,
    amount,
    currency_code,
    budget_owner_id,
    created_at,
    updated_at
from {{ ref('int_budget_lines_enriched') }}