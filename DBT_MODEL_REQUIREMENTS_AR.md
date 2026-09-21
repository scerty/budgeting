# متطلبات نماذج dbt للمنصة المالية

## الغرض

هذه الوثيقة هي العقد التحليلي بين نماذج Django التشغيلية وdbt. تحدد:

- مصادر dbt وأسماء الجداول.
- مسؤولية كل طبقة.
- معنى الصف الواحد في كل نموذج.
- المفاتيح والعلاقات المطلوبة.
- اختبارات الجودة الإلزامية.
- حدود ما ينفذه dbt وما يبقى في Django أو ingestion.

المسار المستهدف:

```text
Django / source adapters
        -> PostgreSQL public
        -> dbt staging
        -> dbt intermediate
        -> dbt analytics
        -> Cube / Angular / Power BI
```

لا يعتمد المسار الجديد على Airbyte أو ClickHouse.

## قواعد عامة

1. كل نموذج يجب أن يعرّف `grain` بوضوح.
2. لا تستخدم الأسماء بدل المعرفات في المفاتيح أو العلاقات.
3. كل مبلغ مالي يجب أن يكون `numeric`/`decimal` وليس `float`.
4. يجب الاحتفاظ بالعملة ومصدر السجل وتاريخ ingestion.
5. لا يخلط dbt بين القيود التشغيلية وقيود التوحيد.
6. لا يحذف dbt السجلات المصدرية؛ يستبعد السجل الملغى عبر `is_deleted` أو يبقي أثره التاريخي حسب سياسة النموذج.
7. لا يعيد dbt تفسير Mapping تاريخي باستخدام أحدث نسخة فقط.
8. أي مصدر لا يملك update/delete metadata يوثق كـ snapshot أو full refresh، ولا يوصف خطأ بأنه incremental.

## طبقات dbt

### Sources

جداول Django الموجودة في schema `public`. يجب تعريفها في `models/staging/sources.yml` مع descriptions واختبارات freshness عندما تتوفر timestamps.
تمت مطابقة قائمة المصادر مع app `finance` في Django: يوجد حاليًا 82 نموذجًا تشغيليًا و82 مصدرًا في `sources.yml` دون مصادر زائدة أو نماذج غير معلنة. جميع هذه النماذج ترث `TimeStampedModel`، لكن freshness لا يطبق بحد زمني عام على master وconfiguration لأن قلة التحديث فيها طبيعية؛ يطبق على جداول الحركة ذات cadence متوقع مثل `finance_expense` باستخدام `updated_at`، وتضاف سياسات خاصة للمصادر الأخرى عند تحديد دورة تحديثها.

### Staging

نماذج `stg_*` قريبة من المصدر، وتنفذ فقط:

- إعادة تسمية الأعمدة إلى أسماء تحليلية ثابتة.
- تحويل الأنواع والتواريخ والعملات إلى صيغة موحدة.
- تنظيف الأكواد بـ `upper(trim(code))`.
- تمرير metadata وحقول الحذف دون تجميع.
- منع duplicate source keys.

لا تضع business joins أو تجميعات شهرية في staging.

### Intermediate

نماذج `int_*` تنفذ joins والتحقق من السياق، مثل ربط المصروف بالقسم والفرع والكيان والحساب. يجب أن تحافظ على grain المصدر أو توثّق أي تغيير صراحة.

### Analytics / Marts

نماذج `dim_*` و`fact_*` وmarts المجمعة. هذه هي الطبقة التي يقرأ منها Cube والتقارير، وليس `public` مباشرة.

## مصادر PostgreSQL المطلوبة

| مصدر Django | نموذج staging المقترح | الغرض |
|---|---|---|
| `finance_organization` | `stg_organizations` | عزل المجموعة ومرجع التقارير |
| `finance_country` | `stg_countries` | الدولة والاختصاص |
| `finance_currency` | `stg_currencies` | عملة الحركة والتقرير |
| `finance_fiscalcalendar` | `stg_fiscal_calendars` | تقويم الكيان |
| `finance_fiscalperiod` | `stg_fiscal_periods` | الفترة المالية |
| `finance_legalentity` | `stg_legal_entities` | الكيان القانوني |
| `finance_ownershipperiod` | `stg_ownership_periods` | الملكية والسيطرة زمنياً |
| `finance_businessunit` | `stg_business_units` | وحدة الأعمال |
| `finance_entitybusinessunitassignment` | `stg_entity_business_unit_assignments` | نطاق وحدة الأعمال |
| `finance_branch` | `stg_branches` | الموقع التشغيلي |
| `finance_department` | `stg_departments` | القسم |
| `finance_departmententityassignment` | `stg_department_entity_assignments` | الأقسام المشتركة بين الكيانات |
| `finance_departmentbranchassignment` | `stg_department_branch_assignments` | نطاق القسم حسب الفرع |
| `finance_costcenter` | `stg_cost_centers` | مركز التكلفة |
| `finance_profitcenter` | `stg_profit_centers` | مركز الربح |
| `finance_project` | `stg_projects` | المشروع أو العقد |
| `finance_groupaccount` | `stg_group_accounts` | دليل حسابات المجموعة |
| `finance_entityaccount` | `stg_entity_accounts` | دليل الحساب المحلي |
| `finance_mappingversion` | `stg_mapping_versions` | نسخة الـ Mapping |
| `finance_accountmapping` | `stg_account_mappings` | ربط المحلي بالمجموعة |
| `finance_accounthierarchy` | `stg_account_hierarchies` | هياكل التقارير المتوازية |
| `finance_accounthierarchynode` | `stg_account_hierarchy_nodes` | عقد تجميع الحسابات |
| `finance_reportgroup` | `stg_report_groups` | مجموعات قوالب التقارير |
| `finance_reporttemplate` | `stg_report_templates` | تعريف التقرير المرتبط بهيكل الحسابات |
| `finance_reportcolumnmodel` | `stg_report_column_models` | نموذج أعمدة قابل لإعادة الاستخدام |
| `finance_reportcolumnmodelitem` | `stg_report_column_model_items` | عناصر توليد الأعمدة |
| `finance_reportcolumn` | `stg_report_columns` | أعمدة actuals والسيناريو والـ variance |
| `finance_reportrunsnapshot` | `stg_report_run_snapshots` | نسخة frozen من نتيجة التقرير |
| `finance_budgetplan` | `stg_budget_plans` | خطة الميزانية |
| `finance_budgetversion` | `stg_budget_versions` | نسخة الميزانية والسيناريو |
| `finance_budgetline` | `stg_budget_lines` | سطر الميزانية |
| `finance_scenario` | `stg_scenarios` | تعريف السيناريو التخطيطي |
| `finance_scenarioversion` | `stg_scenario_versions` | نسخة سيناريو قابلة للقفل والتدقيق |
| `finance_scenarioblend` | `stg_scenario_blends` | دمج actuals والتخطيط حسب نطاق الفترة |
| `finance_importsource` | `stg_import_sources` | مصادر الاستيراد المهيأة |
| `finance_ingestionrun` | `stg_ingestion_runs` | تشغيل الاستيراد |
| `finance_ingestionissue` | `stg_ingestion_issues` | أخطاء وتحذيرات الصفوف |
| `finance_newcodediscovery` | `stg_new_code_discoveries` | الأكواد المكتشفة غير المربوطة |
| `finance_rawexpense` | `stg_raw_expenses` | landing الخام للمصروفات |
| `finance_rawjournalline` | `stg_raw_journal_lines` | landing الخام لأسطر GL |
| `finance_expense` | `stg_expenses` | المصروف التشغيلي/الفعلي |
| `finance_exchangerate` | `stg_exchange_rates` | أسعار الصرف حسب التاريخ والنوع |
| `finance_taxcode` | `stg_tax_codes` | رموز الضرائب |
| `finance_taxrate` | `stg_tax_rates` | معدلات الضرائب الفعالة |
| `finance_supplier` | `stg_suppliers` | الموردون |
| `finance_customer` | `stg_customers` | العملاء |
| `finance_invoice` | `stg_invoices` | رؤوس فواتير AP/AR |
| `finance_invoiceline` | `stg_invoice_lines` | تفاصيل الفواتير |
| `finance_payment` | `stg_payments` | الدفعات |
| `finance_paymentallocation` | `stg_payment_allocations` | توزيع الدفعات على الفواتير |
| `finance_planningassumption` | `stg_planning_assumptions` | افتراضات التخطيط |
| `finance_planningdriver` | `stg_planning_drivers` | محركات التخطيط |
| `finance_drivervalue` | `stg_driver_values` | قيم المحركات حسب الفترة والنطاق |
| `finance_calculationrule` | `stg_calculation_rules` | قواعد الحساب |
| `finance_calculationruledependency` | `stg_calculation_rule_dependencies` | تبعيات قواعد الحساب |
| `finance_calculationrun` | `stg_calculation_runs` | تشغيل محرك الحساب وmetadata التنفيذ |
| `finance_planningfact` | `stg_planning_facts` | نتائج التخطيط المحسوبة بحبيبة صريحة |
| `finance_allocationrule` | `stg_allocation_rules` | قواعد توزيع التكاليف |
| `finance_allocationruleline` | `stg_allocation_rule_lines` | أهداف ونسب التوزيع |
| `finance_encumbrance` | `stg_encumbrances` | الالتزامات غير المحولة إلى actual |
| `finance_workflowdefinition` | `stg_workflow_definitions` | تعريفات سير الموافقات |
| `finance_workflowstep` | `stg_workflow_steps` | خطوات سير الموافقات |
| `finance_approvalrequest` | `stg_approval_requests` | طلبات الاعتماد |
| `finance_approvalaction` | `stg_approval_actions` | أحداث الاعتماد |
| `finance_planningsubmission` | `stg_planning_submissions` | تسليم نسخة السيناريو حسب النطاق |
| `finance_auditlog` | `stg_audit_logs` | سجل التدقيق |
| `finance_journalentry` | `stg_journal_entries` | رؤوس القيود |
| `finance_journalentryline` | `stg_journal_entry_lines` | أسطر القيود المزدوجة |
| `finance_consolidationgroup` | `stg_consolidation_groups` | مجموعات التوحيد |
| `finance_consolidationscope` | `stg_consolidation_scopes` | نطاق الكيانات الداخلة في التوحيد |
| `finance_intercompanypair` | `stg_intercompany_pairs` | أزواج التعاملات البينية |
| `finance_eliminationrule` | `stg_elimination_rules` | قواعد الاستبعاد |
| `finance_consolidationrun` | `stg_consolidation_runs` | دورات التوحيد |
| `finance_eliminationentry` | `stg_elimination_entries` | قيود الاستبعاد الناتجة |
| `finance_minorityinterestentry` | `stg_minority_interest_entries` | حقوق الأقلية |
| `finance_translationadjustment` | `stg_translation_adjustments` | فروق ترجمة العملة |
| `finance_goodwillcalculation` | `stg_goodwill_calculations` | حسابات الشهرة |
| `finance_intercompanyinventoryelimination` | `stg_intercompany_inventory_eliminations` | استبعاد ربح المخزون البيني |
| `finance_intercompanymatch` | `stg_intercompany_matches` | نتائج مطابقة التعاملات البينية |
| `finance_role` | `stg_roles` | تعريفات الصلاحيات على مستوى المنظمة، للاطلاع والتدقيق فقط |
| `finance_userprofile` | `stg_user_profiles` | تفضيلات المستخدم، لا تفرض الصلاحيات |
| `finance_userorgscope` | `stg_user_org_scopes` | نطاقات المستخدمين، لا تستخدم لفرض authorization داخل dbt |

## خريطة النماذج المطلوبة من نموذج البيانات الموحد

هذه هي قائمة النماذج التحليلية المطلوبة بناءً على نماذج Django الحالية. وجود النموذج في هذه القائمة يعني أنه جزء من العقد المستهدف، ولا يعني أنه منفذ في مجلد dbt حاليًا.

### نماذج staging المطلوبة

يجب إنشاء staging لكل مصدر في الجدول السابق، مع الحفاظ على grain المصدر:

```text
stg_organizations
stg_countries
stg_currencies
stg_fiscal_calendars
stg_fiscal_periods
stg_legal_entities
stg_ownership_periods
stg_business_units
stg_entity_business_unit_assignments
stg_branches
stg_departments
stg_department_entity_assignments
stg_department_branch_assignments
stg_cost_centers
stg_profit_centers
stg_projects
stg_group_accounts
stg_entity_accounts
stg_mapping_versions
stg_account_mappings
stg_account_hierarchies
stg_account_hierarchy_nodes
stg_report_groups
stg_report_templates
stg_report_column_models
stg_report_column_model_items
stg_report_columns
stg_report_run_snapshots
stg_budget_plans
stg_budget_versions
stg_budget_lines
stg_scenarios
stg_scenario_versions
stg_scenario_blends
stg_import_sources
stg_ingestion_runs
stg_ingestion_issues
stg_new_code_discoveries
stg_raw_expenses
stg_raw_journal_lines
stg_expenses
stg_exchange_rates
stg_tax_codes
stg_tax_rates
stg_suppliers
stg_customers
stg_invoices
stg_invoice_lines
stg_payments
stg_payment_allocations
stg_planning_assumptions
stg_planning_drivers
stg_driver_values
stg_calculation_rules
stg_calculation_rule_dependencies
stg_calculation_runs
stg_planning_facts
stg_allocation_rules
stg_allocation_rule_lines
stg_encumbrances
stg_workflow_definitions
stg_workflow_steps
stg_approval_requests
stg_approval_actions
stg_planning_submissions
stg_audit_logs
stg_journal_entries
stg_journal_entry_lines
stg_consolidation_groups
stg_consolidation_scopes
stg_intercompany_pairs
stg_elimination_rules
stg_consolidation_runs
stg_elimination_entries
stg_minority_interest_entries
stg_translation_adjustments
stg_goodwill_calculations
stg_intercompany_inventory_eliminations
stg_intercompany_matches
stg_roles
stg_user_profiles
stg_user_org_scopes
```

### نماذج intermediate المطلوبة

```text
int_expenses_enriched
int_budget_lines_enriched
int_business_unit_scope_effective
int_department_scope_effective
int_account_mappings_effective
int_ownership_effective
int_actuals_budget_ready
int_invoices_enriched
int_payments_allocated
int_encumbrances_budget_ready
int_planning_driver_values
int_allocation_rules_effective
int_journal_entries_balanced
int_report_layouts_effective
int_planning_submissions_reconciled
int_scenario_blends_effective
int_calculation_rule_dependencies
int_planning_facts_enriched
int_scenario_blends_effective
int_calculation_rule_dependencies
int_planning_facts_enriched
int_report_layouts_effective
int_planning_submissions_reconciled
```

قواعد هذه النماذج:

- `int_business_unit_scope_effective` يختار Assignment الصالح للكيان وتاريخ الحركة.
- `int_department_scope_effective` يوحد نطاقات Entity وBranch دون مضاعفة صفوف المصروف.
- `int_account_mappings_effective` يختار Mapping المعتمد الفعال في تاريخ الحركة.
- `int_ownership_effective` مطلوب للتقارير التاريخية ويمهد للتوحيد، لكنه ليس مدخلًا لـ `fact_expenses` في MVP الحالي.
- `int_actuals_budget_ready` هو نقطة التوحيد قبل المقارنة، ويجب أن يكون على نفس الأبعاد والفترة والعملة في actual وbudget.
- `int_invoices_enriched` و`int_payments_allocated` يحافظان على علاقة AP/AR دون تكرار رأس الفاتورة بسبب تعدد الأسطر أو التخصيصات.
- `int_encumbrances_budget_ready` يجهز الالتزامات لمعادلة Available Budget دون اعتبارها actual.
- `int_planning_driver_values` يختار قيمة محرك واحدة فعالة لكل فترة ونطاق.
- `int_allocation_rules_effective` يختار قاعدة توزيع معتمدة ويتحقق من مجموع نسبها.
- `int_journal_entries_balanced` يتحقق من توازن المدين والدائن قبل أي fact مستقبلي لأسطر القيود.
- `int_scenario_blends_effective` يحول مكونات الـ blend إلى نطاقات فترات غير متداخلة في نفس الأولوية، ويحتفظ بالأولوية عند وجود طبقات متداخلة مقصودة.
- `int_calculation_rule_dependencies` يعرض graph القواعد ونتيجة كشف الدورات التي نفذها محرك Django؛ لا يعيد dbt تنفيذ التعبيرات.
- `int_planning_facts_enriched` يربط نتيجة التشغيل بالسيناريو والنسخة والفترة والأبعاد، ويحتفظ بـ `calculation_run_id` و`lineage`.
- `int_report_layouts_effective` يتحقق من أعمدة التقرير، ويفصل actuals وscenario وmixed وvariance، لكنه لا ينفذ الحسابات المالية.
- `int_planning_submissions_reconciled` يربط submission بالسيناريو والـ workflow والنطاق التنظيمي، ويكشف النسخ التي لا تملك اعتمادًا مكتملًا.

لا ينفذ dbt صلاحيات `Role` أو `UserOrgScope`. يمكن تحميلها للتدقيق أو reconciliation، لكن filter الأمني يجب أن يطبق في Django/API أو طبقة semantic مضبوطة.

### نماذج dimensions المطلوبة

```text
dim_organization
dim_country
dim_currency
dim_fiscal_period
dim_legal_entity
dim_branch
dim_department
dim_cost_center
dim_profit_center
dim_business_unit
dim_project
dim_group_account
dim_entity_account
dim_scenario
dim_scenario_version
dim_budget_version
dim_supplier
dim_customer
dim_tax_code
dim_date
```

لا نحتاج إلى `dim_fiscal_calendar` مستقل في المرحلة الحالية؛ يمر `calendar_id` وخصائص التقويم إلى `dim_fiscal_period`، ويمكن فصل Dimension مستقل لاحقًا إذا أصبح التقويم كيانًا تقريريًا بحد ذاته.

### نماذج facts وmarts المطلوبة

```text
fact_expenses
fact_budget
fact_invoices
fact_payments
fact_encumbrances
fact_planning_driver_values
fact_planning
budget_vs_actual
expenses_by_branch
expenses_by_month
expenses_by_branch_month
```

يبقى `fact_journal_lines` ضمن مرحلة لاحقة حتى يثبت نشر دفتر الأستاذ والتوحيد؛ وجود `stg_journal_entries` و`stg_journal_entry_lines` لا يعني أن actuals المحاسبية أصبحت مصدر التقارير الحالي.

### نماذج الاستثناءات المطلوبة

يجب ألا تختفي السجلات غير القابلة للربط داخل joins. الحد الأدنى من exception models هو:

```text
exceptions_unmapped_expenses
exceptions_unmapped_accounts
exceptions_invalid_organization_links
exceptions_invalid_effective_assignments
exceptions_duplicate_source_records
```

كل exception model يحتفظ بالمفتاح المصدر، وسبب الاستثناء، وتاريخ الاكتشاف، واسم النموذج المصدر. لا يدخل السجل في fact المنشور إلا بعد تطبيق سياسة واضحة ومختبرة.

### نماذج مستقبلية خارج MVP

هذه النماذج لا تُبنى ضمن عقد المصروفات والميزانية الحالي:

```text
fact_journal_lines
fact_intercompany
fact_eliminations
consolidated_financials
```

تُبنى هذه facts بعد نشر نتائج `ConsolidationRun` والتحقق من قواعد المطابقة والاستبعاد في Django أو source adapter. لا يستخدم `fact_expenses` بديلًا عن `fact_journal_lines`.

## نماذج staging: الحد الأدنى للأعمدة

### `stg_organizations`

Grain: صف واحد لكل `organization_id`.

الأعمدة المطلوبة: `organization_id`, `organization_code`, `legal_name`, `display_name`, `default_reporting_currency_id`, `default_fiscal_calendar_id`, `timezone`, `status`, `created_at`, `updated_at`.

### `stg_legal_entities`

Grain: صف واحد لكل `legal_entity_id`.

الأعمدة المطلوبة: `legal_entity_id`, `organization_id`, `entity_code`, `legal_name`, `country_id`, `functional_currency_id`, `reporting_currency_id`, `fiscal_calendar_id`, `parent_entity_id`, `consolidation_method`, `valid_from`, `valid_to`, `status`.

### `stg_branches`

Grain: صف واحد لكل `branch_id`.

يجب تمرير `legal_entity_id`, `country_id`, `branch_code`, `branch_name`, `city`, `is_active`, `created_at`, `updated_at`. لا تفترض أن `branch_code` فريد على مستوى المجموعة؛ المفتاح التجاري هو `legal_entity_id + branch_code`.

### `stg_departments`

Grain: صف واحد لكل `department_id`.

يجب تمرير `department_id`, `department_code`, `department_name`, `branch_id`, `legal_entity_id`, `parent_department_id`, `is_active`, `created_at`, `updated_at`.

القسم قد يكون مركزيًا أو مشتركًا؛ لا تستخدم `branch_id` وحده لتحديد نطاقه عندما تكون assignment tables موجودة.

### `stg_expenses`

Grain: صف واحد لكل مصروف تشغيلي.

المفتاح التحليلي المفضل:

```text
source_system + source_entity + source_record_id
```

يجب تمرير: `expense_id`, `source_system`, `source_entity`, `source_record_id`, `record_hash`, `amount`, `currency`, `expense_date`, `description`, `legal_entity_id`, `branch_id`, `department_id`, `entity_account_id`, `group_account_id`, `cost_center_id`, `profit_center_id`, `business_unit_id`, `project_id`, `is_deleted`, `created_at`, `updated_at`, `ingested_at`, `source_created_at`, `source_updated_at`.

السجلات الحالية تستخدم حقل `currency` النصي للتوافق التاريخي، مع وجود `currency_master_id` للمرجع. يجب أن يوحّد staging الناتج إلى `currency_code` ويختبر تطابق المرجعين.

### `stg_raw_expenses`

Grain: صف واحد لكل سجل مصدر خام، بمفتاح `source_system + source_entity + source_record_id`.

لا يطبق هذا النموذج mapping داخليًا. يحتفظ بـ `source_account_code`, `source_branch_code`, `source_department_code`, `source_cost_center_code`, `record_hash`, `source_payload`, `is_deleted`, و`ingestion_run_id` لاستخدامها في reconciliation.

### `stg_budget_lines`

Grain: صف واحد لكل `budget_line_id`، مع مفتاح عمل مركب يطابق:

```text
version_id
+ legal_entity_id
+ fiscal_period_id
+ group_account_id
+ entity_account_id
+ branch_id
+ department_id
+ cost_center_id
+ profit_center_id
+ business_unit_id
+ project_id
```

يجب تمرير `amount`, `currency_id`, ومالك الميزانية، وعدم تحويل الميزانية إلى actuals داخل staging.

### `stg_scenarios` و`stg_scenario_versions`

`stg_scenarios` يحتفظ بصف واحد لكل `scenario_id`، مع `organization_id`, `code`,
`scenario_type`, `status`, و`is_active`.

`stg_scenario_versions` يحتفظ بصف واحد لكل `scenario_version_id`، مع
`scenario_id`, `version_number`, `status`, `is_final`, `locked_at`, `locked_by`,
و`based_on_id`. لا يستخدم `BudgetVersion.scenario` النصي كبديل عندما يكون
`scenario_version_id` متاحًا؛ يبقى الحقل النصي للتوافق مع الإصدارات القديمة.

### `stg_scenario_blends`

Grain: صف واحد لكل مكوّن blend.

المفتاح: `scenario_blend_id`. يجب تمرير `result_version_id`, `source_kind`,
`source_version_id`, `fiscal_period_from_id`, `fiscal_period_to_id`, و`priority`.

- `source_kind = actuals` يعني أن `source_version_id` NULL.
- `source_kind = planning` يتطلب `source_version_id`.
- لا يجوز إسقاط المكونات المتداخلة؛ يختار `int_scenario_blends_effective` الأولوية
    الموثقة، ويفشل عند تداخل مكونين في نفس الأولوية.
- يجب اختبار أن المصدر والنتيجة ينتميان إلى المنظمة نفسها وأن الفترتين تستخدمان
    التقويم نفسه.

### `stg_calculation_rules` و`stg_calculation_rule_dependencies`

Grain القاعدة: صف واحد لكل `calculation_rule_id`. تمرر staging الحقول
`rule_type`, `priority`, `expression`, `input_keys`, `scenario_version_id`,
`target_group_account_id`, وeffective dates كما هي؛ لا ينفذ SQL أو Python التعبير.

Grain التبعية: صف واحد لكل `rule_id + depends_on_id`. يجب اختبار عدم وجود self-loop
وأن graph القواعد acyclic. مصدر الحقيقة لكشف الدورات هو محرك Django، ويجب أن يظهر
الفشل في reconciliation بدل إنتاج نتائج جزئية.

### `stg_calculation_runs` و`stg_planning_facts`

`stg_calculation_runs` يحتفظ بصف واحد لكل تشغيل، مع `scenario_version_id`, الحالة،
أوقات البدء والانتهاء، و`input_snapshot`.

`stg_planning_facts` يحتفظ بصف واحد لكل نتيجة عند الحبيبة التالية:

```text
calculation_run_id
+ scenario_version_id
+ fiscal_period_id
+ legal_entity_id
+ group_account_id
+ entity_account_id
+ branch_id
+ department_id
+ cost_center_id
+ profit_center_id
+ business_unit_id
+ project_id
```

يجب تمرير `source_kind`, `source_rule_id`, `amount`, `currency_id`, و`lineage`.
لا تجمع هذه النتائج مع `fact_budget` في staging، ولا تستخدمها كبديل عن
`fact_journal_lines` أو actuals.

### `stg_report_*`

هذه المصادر هي configuration metadata وليست facts مالية:

- `stg_report_groups`: صف واحد لكل `report_group_id`، مع الحفاظ على parent tree.
- `stg_report_templates`: صف واحد لكل `report_template_id`، مع `organization_id`,
    `account_hierarchy_id`, scope الافتراضي، و`created_by`.
- `stg_report_column_models`: صف واحد لكل نموذج أعمدة قابل لإعادة الاستخدام.
- `stg_report_column_model_items`: صف واحد لكل `column_model_id + sort_order`، مع
    نوع المصدر، offsets، scenario version، وcutover عند mixed.
- `stg_report_columns`: صف واحد لكل عمود داخل template. يجب تمرير مراجع variance
    وعدم حذفها داخل staging.
- `stg_report_run_snapshots`: صف واحد لكل snapshot frozen، مع `run_period_id`,
    `data_as_of`, `source_hash`, و`result_data`.

قواعد الجودة:

- كل template وgroup وcolumn model ينتمي إلى Organization واحدة.
- hierarchy وscenario version وكل dimension scope تتبع المنظمة نفسها.
- عمود actuals لا يحمل scenario، وعمود scenario يتطلب scenario version، وmixed
    يتطلب scenario version وcutover، وvariance يشير إلى عمودين من نفس template.
- لا ينفذ dbt layout أو variance أو mixed calculation من JSON configuration. يقوم
    service/worker في Django بحل layout، ثم يقرأ facts المالية من analytics.
- `result_data` في snapshot هو artifact frozen وليس مصدرًا بديلًا لـ
    `fact_expenses`, `fact_budget`, أو `fact_planning`.

### `stg_planning_submissions`

Grain: صف واحد لكل `planning_submission_id`، مع
`scenario_version_id + legal_entity_id + branch_id + department_id` كـ business
scope، و`workflow_id`, `current_step_id`, `status`, وحقول القرار.

يجب اختبار أن workflow والسيناريو والنطاق التنظيمي ينتمون إلى Organization نفسها،
وأن current step تابع لذلك workflow. لا يعتبر scenario version معتمدًا بالكامل
لمجرد وجود submission واحد؛ يجب أن تحدد طبقة orchestration مجموعة submissions
المطلوبة قبل نقل النسخة إلى حالة locked.

## نماذج intermediate المطلوبة

### `int_expenses_enriched`

Grain: صف واحد لكل مفتاح المصروف المصدر.

المسؤوليات:

- ربط المصروف بالقسم والفرع والكيان.
- التحقق من اتساق `branch.legal_entity_id` مع المصروف.
- إثراء الاسم والكود من الأبعاد المرجعية.
- استبعاد `is_deleted = true` من fact الحالي، مع إبقاء نموذج audit عند الحاجة.
- عدم مضاعفة الصفوف بسبب assignment أو mapping؛ استخدم اختيار السجل الفعال حسب تاريخ المصروف.
- `branch_id` اختياري في Django: قد يأتي من `Expense.branch` أو من فرع القسم، وقد يبقى NULL للقسم المركزي. يحتفظ `fact_expenses` بهذه السجلات، بينما تستخدم marts المبنية حسب الفرع `inner join` مع `dim_branch` وتستبعدها عمدًا؛ أما `expenses_by_month` فتشملها.

### `int_budget_lines_enriched`

Grain: صف واحد لكل `budget_line_id`.

المسؤوليات:

- ربط النسخة بالخطة والسيناريو والحالة.
- ربط الفترة بالـ fiscal calendar الخاص بالكيان.
- التحقق من أن الحساب والكيان ينتميان إلى المنظمة نفسها.
- توحيد currency code وقياس المبلغ.

### `int_account_mappings_effective`

Grain: صف واحد لكل mapping صالح للحساب والتاريخ.

قواعد الاختيار:

- تاريخ الحركة يقع بين `valid_from` و`valid_to`.
- تؤخذ نسخة mapping المعتمدة فقط في تقارير المجموعة.
- لا يسمح بأكثر من mapping فعال لنفس local account إلا عندما يكون `mapping_type = one_to_many` وله نسب توزيع موثقة.
- الحساب غير المربوط يظهر في exception model ولا يختفي بصمت.

### `int_actuals_budget_ready`

نموذج مطلوب في مسار `budget_vs_actual` لتوحيد حقول actual وbudget قبل المقارنة. يجب أن يحافظ على `legal_entity_id`, `group_account_id`, `branch_id`, `department_id`, `cost_center_id`, `project_id`, `fiscal_period_id`, `currency_code`, و`scenario`. إذا نُفذت هذه العملية داخل نموذج `budget_vs_actual` مباشرة، فيجب توثيق التكافؤ واختباره بدل حذف العقد منطقيًا.

## نماذج الأبعاد

| النموذج | Grain | المفتاح |
|---|---|---|
| `dim_organization` | منظمة واحدة | `organization_id` |
| `dim_country` | دولة واحدة | `country_id` |
| `dim_currency` | عملة واحدة | `currency_id` / `currency_code` |
| `dim_fiscal_period` | فترة واحدة داخل تقويم | `fiscal_period_id` |
| `dim_legal_entity` | كيان قانوني واحد | `legal_entity_id` |
| `dim_branch` | فرع واحد | `branch_id` |
| `dim_department` | قسم واحد | `department_id` |
| `dim_cost_center` | مركز تكلفة واحد | `cost_center_id` |
| `dim_profit_center` | مركز ربح واحد | `profit_center_id` |
| `dim_business_unit` | وحدة أعمال واحدة | `business_unit_id` |
| `dim_project` | مشروع واحد | `project_id` |
| `dim_group_account` | حساب مجموعة واحد | `group_account_id` |
| `dim_entity_account` | حساب محلي واحد | `entity_account_id` |
| `dim_scenario` | سيناريو تخطيطي واحد | `scenario_id` |
| `dim_scenario_version` | نسخة سيناريو واحدة | `scenario_version_id` |
| `dim_budget_version` | نسخة ميزانية واحدة | `budget_version_id` |
| `dim_date` | يوم تقويمي واحد | `date_key` |

الأبعاد التاريخية التي تعتمد على `valid_from/valid_to` يجب ألا تستخدم الحالة الحالية فقط عند تحليل حركة قديمة.

## نماذج facts وmarts

### `fact_expenses`

Grain: صف واحد لكل مصروف فعلي غير محذوف.

المفتاح الفريد: `source_system + source_entity + source_record_id`، مع إبقاء `expense_id` كمفتاح تشغيل داخلي.

الأعمدة الأساسية: مفاتيح كل الأبعاد، `date_key`, `amount`, `currency_code`, `description`, `record_hash`, `created_at`, `updated_at`, `ingested_at`.

### `fact_budget`

Grain: صف واحد لكل `BudgetLine` عند مستوى التفاصيل المحفوظ في Django.

يجب أن يحتوي على `budget_version_id`, `scenario_version_id` عند توفره، `scenario`,
`status`, `legal_entity_id`, `fiscal_period_id`, `group_account_id`, optional
local/organization dimensions, `amount`, و`currency_code`.

لا تجمع `fact_budget` مع `fact_expenses` إلا بعد التطبيع إلى نفس الفترة والحساب والأبعاد. لا تستخدم `budget_version_id` كبديل عن `scenario` في التقارير.

### `fact_planning`

Grain: صف واحد لكل `PlanningFact` عند grain التشغيل الموثق في
`stg_planning_facts`.

يحتوي على `calculation_run_id`, `scenario_id`, `scenario_version_id`,
`fiscal_period_id`, كل مفاتيح الأبعاد المتاحة، `source_kind`, `source_rule_id`,
`amount`, `currency_code`, و`lineage`. يجب اختبار uniqueness على grain الكامل
قبل materialization. لا يجوز اعتبار `source_kind = calculated` actualًا، ولا
استبدال هذا النموذج بـ `fact_budget` لأن budget يمثل الإدخال المعتمد بينما
planning fact يمثل نتيجة تشغيل قابلة لإعادة البناء.

### `scenario_blended_budget`

نموذج intermediate أو mart اختياري لنشر نتيجة ScenarioBlend. Grainه صف واحد لكل
`result_version_id + fiscal_period_id + financial dimensions`. يطبق أعلى `priority`
المسموح به عند التداخل، ويمنع نشر أكثر من قيمة فعالة لنفس grain. عند اختيار
`source_kind = actuals` تؤخذ القيم من مسار actual المعتمد، وعند `planning` تؤخذ
من `fact_planning` أو `fact_budget` وفق `source_version_id` الموثق.

### `budget_vs_actual`

Grain افتراضي: صف واحد لكل:

```text
organization_id
+ legal_entity_id
+ fiscal_period_id
+ group_account_id
+ branch_id
+ department_id
+ cost_center_id
+ project_id
+ scenario
```

المقاييس:

```text
budget_amount
actual_amount
variance_amount = actual_amount - budget_amount
variance_percentage
```

يجب تعريف سلوك القسمة على صفر، وتحديد currency/reporting currency قبل الجمع بين كيانات متعددة.

### Marts الحالية المتوافقة

يستمر دعم:

- `expenses_by_branch`: صف واحد لكل فرع.
- `expenses_by_month`: صف واحد لكل شهر.
- `expenses_by_branch_month`: صف واحد لكل `branch_id + month_key`.

هذه marts مبنية من `fact_expenses` وليست مصادر مستقلة. يجب أن تبقى filters الخاصة بـ Cube متوافقة مع `branch_code` و`month_key`.

## اختبارات dbt الإلزامية

### اختبارات المفاتيح

- `not_null` و`unique` لكل primary key في dimension.
- uniqueness لمفتاح المصروف المصدر المركب.
- uniqueness لـ `budget_line` على grain الموثق.
- uniqueness لـ `branch_id + month_key` في `expenses_by_branch_month`.

### اختبارات العلاقات

- المصروف يرتبط بقسم موجود.
- القسم يرتبط بفرع أو نطاق assignment صالح.
- الفرع والـ cost center يتبعان الكيان نفسه عند تطبيق البعد.
- الحساب المحلي يتبع الكيان.
- Group Account يتبع المنظمة.
- الفترة تتبع fiscal calendar الخاص بالكيان.
- كل foreign key في facts يرتبط بالـ dimension المقابل.

### اختبارات الاتساق المالي

- `amount` غير NULL وموجب للمصروفات التي لا تمثل reversal.
- currency code من قائمة العملات المرجعية وبطول ISO صحيح.
- لا توجد actuals من `is_deleted = true` في fact الحالي.
- mapping المعتمد لا يملك أكثر من نتيجة فعالة غير مبررة.
- نسب one-to-many لا تتجاوز 100% حسب سياسة التوزيع.
- `variance_percentage` لا يفشل عند `budget_amount = 0`.

### اختبارات freshness وreconciliation

- freshness لـ `finance_expense.updated_at` أو `source_updated_at` عند توفره.
- freshness لـ `finance_scenarioversion.updated_at` و`finance_calculationrun.updated_at` عند تشغيل التخطيط.
- عدد السجلات في `stg_expenses` يطابق السجلات الفعالة في المصدر ضمن سياسة الحذف.
- مجموع `fact_expenses` يطابق مجموع staging بعد استبعاد السجلات المحذوفة والتالفـة.
- كل `RawExpense` مرتبط بـ `IngestionRun` ناجح أو يظهر في exception report.
- exceptions للحسابات أو الأبعاد غير المربوطة لا تساوي صفرًا بصمت؛ إما تمر باعتماد أو تفشل الدورة.
- كل `PlanningFact` يرتبط بتشغيل ناجح أو يظهر في تقرير تشغيل فاشل.
- لا توجد دورة في `calculation_rule_dependency`، ولا توجد نتيجتان فعالتان لنفس
    scenario blend priority والـ financial grain.
- لا تختلط `scenario_version_id` بين `CalculationRun` و`PlanningFact` أو بين
    القاعدة والسيناريو الذي نفذت فيه.

## Materialization وrefresh

المرحلة الأولى:

```text
staging       view
intermediate  view أو table حسب حجم joins
dimensions    table
facts         table
marts         table
```

بعد إثبات idempotency وupdate/delete/backfill يمكن تحويل `fact_expenses` إلى incremental مع:

```text
unique_key = source_system + source_entity + source_record_id
```

لا تستخدم incremental قبل تحديد affected partitions في marts الشهرية. يبقى `dbt build --full-refresh` مسار recovery موثقًا، وليس أمر التشغيل اليومي.

## Refresh contract

```text
ingestion run
    -> raw landing
    -> source/staging checks
    -> dbt build
    -> dbt tests
    -> publish analytics models
    -> Cube refresh/invalidation
```

أي فشل في ingestion أو dbt يمنع إعلان دورة refresh ناجحة. لا يقرأ Cube من raw، ولا يقرأ dashboard من جداول Django التشغيلية مباشرة.

## حالة تنفيذ نماذج dbt

### منفذ حاليًا

المسار الأساسي المنفذ والمختبر هو:

```text
public Django sources
     -> staging: master data, expenses, journal lines, budget, scenarios,
         drivers, calculation runs, planning facts, AP/AR, encumbrances
     -> intermediate: enrichment, effective scopes, mapping, allocation,
         scenario blends, actual/budget normalization, planning publication
     -> analytics dimensions and facts
     -> reconciliation and exception models
```

ويشمل ذلك النماذج التالية:

```text
dim_organization, dim_country, dim_currency, dim_fiscal_period,
dim_legal_entity, dim_branch, dim_department, dim_cost_center,
dim_profit_center, dim_business_unit, dim_project, dim_group_account,
dim_entity_account, dim_scenario, dim_scenario_version, dim_budget_version,
dim_supplier, dim_customer, dim_tax_code, dim_date
fact_expenses, fact_journal_lines, fact_budget, fact_planning_driver_values,
fact_planning, fact_invoices, fact_payments, fact_encumbrances
budget_vs_actual, reconciliation_budget, reconciliation_planning
exceptions_unmapped_expenses, exceptions_unmapped_accounts,
exceptions_invalid_organization_links, exceptions_invalid_effective_assignments,
exceptions_duplicate_source_records
expenses_by_branch
expenses_by_month
expenses_by_branch_month
```

تم تنفيذ اختبارات staging والمفاتيح والعلاقات والحبيبات وreconciliation؛ آخر تحقق
كامل نجح بـ `399/399` دون warnings أو errors. `fact_planning` لا ينشر إلا نتائج
`CalculationRun` ذات الحالة `succeeded`، و`budget_vs_actual` يطبع actuals وbudget
على نفس الفترة والأبعاد والعملة قبل المقارنة.

يوجد fixture اختياري قابل لإعادة التشغيل للتحقق populated:

```bash
python manage.py seed_planning_demo
```

### متبق خارج core المالي الحالي

هذه المصادر ما زالت معرفة في `sources.yml`، لكن إسقاطاتها ليست جزءًا من MVP
الميزانية والتخطيط المنشور:

```text
stg_account_hierarchies
stg_account_hierarchy_nodes
stg_report_groups
stg_report_templates
stg_report_column_models
stg_report_column_model_items
stg_report_columns
stg_report_run_snapshots
stg_import_sources
stg_ingestion_runs
stg_ingestion_issues
stg_new_code_discoveries
stg_workflow_definitions
stg_workflow_steps
stg_approval_requests
stg_approval_actions
stg_planning_submissions
stg_audit_logs
stg_journal_entries
stg_journal_entry_lines
stg_consolidation_groups
stg_consolidation_scopes
stg_intercompany_pairs
stg_elimination_rules
stg_consolidation_runs
stg_elimination_entries
stg_minority_interest_entries
stg_translation_adjustments
stg_goodwill_calculations
stg_intercompany_inventory_eliminations
stg_intercompany_matches
stg_roles
stg_user_profiles
stg_user_org_scopes
```

أما `stg_roles` و`stg_user_profiles` و`stg_user_org_scopes` فهي metadata اختيارية
للتدقيق، ولا تدخل في facts المالية ولا تفرض authorization.

### مؤجل خارج MVP

```text
fact_intercompany
fact_eliminations
consolidated_financials
```

## ما لا ينفذه dbt

- authentication أو pagination للمصادر.
- retry أو orchestration للـ adapters.
- فرض صلاحيات المستخدمين.
- إنشاء قيود double-entry.
- تعديل القيود المحلية أو إنشاء قيود consolidation داخل public.
- تخمين mapping مفقود أو توزيع مبلغ بلا قاعدة معتمدة.

## عقد Cube وDashboard

يقرأ Cube من `analytics` فقط، ويستخدم measures موحدة مثل:

```text
Actual Amount
Budget Amount
Variance Amount
Variance Percentage
Expense Count
```

العقود الحالية في `cube/schema` هي:

```text
ExpensesByBranch, ExpensesByMonth
Budget, BudgetVsActual, Planning, PlanningDrivers, JournalLines
```

ويقرأ dashboard مقارنات `BudgetVsActual` ونتائج `Planning` بجانب marts
المصروفات. لا توجد في هذه العقود أي قراءة مباشرة من ERPNext أو Airbyte أو ClickHouse.

تحتوي عقود المقارنة والتخطيط على labels وصفية قابلة للفلاتر، وليس IDs فقط، مثل:

```text
organization_code / organization_name
fiscal_period_code / fiscal_period_name / fiscal_year
legal_entity_code
group_account_code / group_account_name
branch_code / branch_name
department_code / department_name
scenario_version_code / scenario_version_name
```

وتستخدم الواجهة هذه الحقول لبناء context موحد للفترة والمنظمة ونسخة السيناريو
والفرع، ثم تمرر الفلاتر إلى Cube قبل عرض measures.

أضيفت مقارنة شهرية في `budget_vs_actual_month`. وبما أن `budget_line` الحالي
مرتبط بالفترة المالية ولا يحمل شهرًا، يوزع المارت الميزانية المعتمدة بالتساوي
على أشهر الفترة. يبقى مجموع التوزيع مساويًا للميزانية الأصلية، وتعرض الواجهة
المقارنة حسب `group_account` وحسب `branch` مع actuals مأخوذة من `expense_date`.

مصدر actuals التشغيلي هو `fact_journal_lines` للسطور القادمة من ERPNext، بعد
ربط الشركة والكيان والحساب ومركز التكلفة والفترة المالية. تبقى سجلات
`source_system = 'django'` fallback للـ demo فقط عندما لا توجد ERPNext journals
لنفس المنظمة، حتى لا تختلط بيانات الاختبار مع البيانات التشغيلية أو تتكرر.

إذا لم يرسل ERPNext branch صريحًا أو لم يكن cost center مربوطًا بفرع في Django،
يبقى `branch_id` للـ journal actual فارغًا. عندها يظهر actual في تجميع المجموعة
لكن لا ينسب إلى فرع حتى يتم تعريف mapping صحيح لمراكز التكلفة.

والأبعاد الأساسية:

```text
Organization
Legal Entity
Country
Branch
Department
Cost Center
Business Unit
Project
Group Account
Fiscal Period
Scenario
Scenario Version
```

أي تغيير في grain أو اسم measure يجب أن يحدّث هذا العقد واختبارات Cube قبل ربط dashboard جديد.

## ترتيب التنفيذ المقترح

1. تحديث `sources.yml` لكل جداول Django الجديدة.
2. بناء staging للمنظمة والكيان والعملة والفترة والفرع والقسم.
3. بناء `stg_expenses` و`int_expenses_enriched` مع اختبارات uniqueness والعلاقات.
4. بناء `dim_*` الأساسية و`fact_expenses`.
5. بناء staging وfact للميزانية.
6. إضافة `int_account_mappings_effective` وexception models.
7. بناء `budget_vs_actual` ثم marts الحالية.
8. ربط Cube واختبار filters الحالية.
9. اختبار INSERT وUPDATE وDELETE وretry وfull recovery.
10. بعد نجاح ذلك فقط، إضافة incremental وscheduling.

## قرار المرحلة

نماذج Django الحالية توفر foundation تشغيلية تشمل `AccountHierarchy`, `ConsolidationRun`,
`IntercompanyMatch` و`EliminationEntry`. ما يزال نشر facts المحاسبية والتوحيدية في dbt
مؤجلًا، ولا يجوز إعادة استخدام `fact_expenses` كبديل لدفتر الأستاذ العام.