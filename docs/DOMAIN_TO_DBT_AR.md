# خريطة المجال إلى dbt

dbt يقرأ مصادر Django من `public` وينشر النماذج التحليلية في `analytics`. وجود مصدر في `sources.yml` لا يعني أن SQL الخاص به منفذ.

## 1. الحالة الحالية

المسار المنفذ حاليًا:

```text
Django public sources
    -> dbt staging
    -> dbt intermediate
    -> analytics dimensions/facts/marts
    -> Cube
```

`healthcheck` نموذج تشغيلي لفحص dbt وليس نموذجًا ماليًا.

العقد الكامل للمصادر والـ backlog موجود في [DBT_MODEL_REQUIREMENTS_AR.md](../DBT_MODEL_REQUIREMENTS_AR.md).
لتحقق populated يمكن تشغيل `python manage.py seed_planning_demo` ثم إعادة `dbt build`.

## 2. خريطة الإسقاطات

| مفهوم المجال | Django source | dbt projection | grain الأساسي | الحالة |
|---|---|---|---|---|
| المنظمة | `finance_organization` | `stg_organizations`, `dim_organization` | صف لكل `organization_id` | منفذ |
| الكيان القانوني | `finance_legalentity` | `stg_legal_entities`, `dim_legal_entity` | صف لكل `legal_entity_id` | منفذ |
| الفترة | `finance_fiscalperiod` | `stg_fiscal_periods`, `dim_fiscal_period` | صف لكل `fiscal_period_id` | منفذ |
| الحسابات | `finance_groupaccount`, `finance_entityaccount` | staging + dimensions | صف لكل account id | منفذ |
| الربط | `finance_accountmapping` | `int_account_mappings_effective` | mapping صالح للحساب والتاريخ | منفذ |
| الهيكل | `finance_accounthierarchy*` | `stg_account_hierarchies*` | صف لكل hierarchy/node | مخطط |
| فرع | `finance_branch` | `stg_branches`, `dim_branch` | صف لكل `branch_id` | منفذ |
| قسم | `finance_department` | `stg_departments`, `dim_department` | صف لكل `department_id` | منفذ |
| مصروف | `finance_expense` | `stg_expenses`, `int_expenses_enriched`, `fact_expenses` | صف لكل `expense_id` | منفذ |
| فواتير | `finance_invoice*` | `stg_invoices*`, `int_invoices_enriched`, `fact_invoices` | صف لكل invoice line منشور | منفذ |
| دفعات | `finance_payment*` | `stg_payments*`, `int_payments_allocated`, `fact_payments` | صف لكل دفعة مع allocated/unallocated | منفذ |
| ميزانية | `finance_budget*` | `stg_budget_*`, `int_budget_lines_enriched`, `fact_budget` | صف لكل `budget_line_id` | منفذ |
| سيناريو | `finance_scenario*` | `stg_scenario_*`, `fact_planning`, `budget_vs_actual` | planning grain معلن | منفذ |
| drivers | `finance_planningdriver`, `finance_drivervalue` | `stg_*`, `int_planning_driver_values`, `fact_planning_driver_values` | قيمة driver لكل فترة ونطاق | منفذ |
| التزام | `finance_encumbrance` | `stg_encumbrances`, `fact_encumbrances` | صف لكل encumbrance | منفذ |
| قيد محاسبي | `finance_journalentry*` | `fact_journal_lines`, `int_journal_entries_balanced` | رأس/سطر القيد | منفذ للتحقق، fact قائم |
| توحيد | `finance_consolidation*` | staging ثم `fact_intercompany`/`fact_eliminations` | حسب run والكيان والحساب | مؤجل |
| تعريف تقرير | `finance_report*` | `stg_report_*`, `int_report_layouts_effective` | metadata لكل template/column | مخطط |
| اعتماد | `finance_workflow*`, `finance_approval*` | staging/reconciliation فقط | صف لكل حدث أو طلب | لا يفرض صلاحيات |

Cube يقرأ من `analytics` فقط عبر العقود `Budget`, `BudgetVsActual`, `Planning`,
`PlanningDrivers`, `JournalLines` وmarts المصروفات. لا يتصل Cube بـ ERPNext، ولا
بـ Airbyte أو ClickHouse. تعرض عقود الميزانية والتخطيط labels المنظمة والفترة
والكيان والحساب والفرع والقسم، وتستخدمها الواجهة في context filters وdrill-down
بدل عرض المعرفات الرقمية وحدها.

وللمقارنة الشهرية يستخدم Cube عقد `BudgetVsActualMonth`: actuals تعتمد على شهر
`expense_date`، أما budget الحالي فيوزع بالتساوي على أشهر الفترة المالية لعدم
وجود شهر على budget line. يعرض dashboard هذا العقد في تجميعين مستقلين حسب الحساب
المجموعة وحسب الفرع.

في التشغيل، actuals لا تعتمد على seed Django: مسار ERPNext هو
`RawJournalLine -> fact_journal_lines -> int_actuals_budget_ready`. ويستخدم
المارت demo records من `finance_expense` فقط كـ fallback عندما لا توجد journals
قادمة من ERPNext للمنظمة، لمنع double counting أثناء التطوير المحلي.

تجميع branch يتطلب أن يحتوي ERPNext على branch أو أن يكون cost center مربوطًا
بـ branch في Django؛ journal الحالي ذو cost center عام مثل `Main - FDD` يظهر
بـ branch فارغ إلى أن يضاف هذا الربط.

## 3. الحقول التي لا يجوز فقدها

### `stg_expenses`

يجب تمرير:

```text
expense_id
source_system + source_entity + source_record_id
record_hash
amount
currency_code + currency_master_id
expense_date
description
legal_entity_id + branch_id + department_id
entity_account_id + group_account_id
cost_center_id + profit_center_id + business_unit_id + project_id
is_deleted
ingested_at + source_created_at + source_updated_at
created_at + updated_at
```

### `fact_expenses`

Grain: صف واحد لكل مصروف فعلي غير محذوف. يحتفظ بمفتاح التشغيل والمفتاح المصدر والبعد المالي. `branch_id` اختياري؛ إذ قد يكون القسم مركزيًا أو يأتي الفرع من `Expense.branch` مباشرة.

`fact_expenses` يحتفظ بسجل بلا فرع، بينما marts الفرعية حسب الفرع تستخدم `inner join` مع `dim_branch`. لذلك:

- `expenses_by_branch` لا يمثل المصروفات بلا فرع.
- `expenses_by_month` يشمل المصروفات بلا فرع.
- لا يجوز اعتبار عدم ظهور المصروف في branch mart حذفًا من fact.

### `fact_budget`

Grain: صف واحد لكل `BudgetLine` عند تفاصيل الأبعاد المحفوظة. لا يخلط مع actuals قبل توحيد الفترة والحساب والعملة والأبعاد.

### `fact_planning`

Grain: grain `PlanningFact` الكامل:

```text
calculation_run_id
scenario_version_id
fiscal_period_id
legal_entity_id
group_account_id
entity_account_id
branch_id
department_id
cost_center_id
profit_center_id
business_unit_id
project_id
```

النتيجة التخطيطية ليست actual وليست بديلًا عن `fact_journal_lines`.

## 4. مراحل dbt ومسؤوليتها

| الطبقة | ما تفعله | ما لا تفعله |
|---|---|---|
| Source | تعريف جدول Django وmetadata وfreshness الانتقائي | لا تغير المصدر |
| Staging | أسماء وأنواع وتنظيف وتمرير metadata | لا تنفذ business aggregation |
| Intermediate | joins، effective dating، كشف عدم الاتساق | لا تفرض صلاحيات المستخدم |
| Dimension | أبعاد وصفية مستقرة للتقارير | لا تستبدل master data في Django |
| Fact | أحداث وقيم مالية عند grain ثابت | لا تنشئ قيودًا تشغيلية |
| Mart | مقارنة وتجميع جاهز للاستهلاك | لا يكون مصدر الحقيقة التشغيلي |

## 5. الاختبارات المطلوبة

- `not_null` و`unique` للمفاتيح الأساسية.
- `relationships` لكل foreign key تحليلي.
- uniqueness على grain كل fact، وليس على surrogate id فقط.
- استبعاد `is_deleted` من facts الحالية.
- عدم مضاعفة الصفوف بسبب assignments أو one-to-many mappings.
- توازن journal entries قبل نشر fact دفتر الأستاذ.
- عدم نشر `PlanningFact` من run فاشل.
- reconciliation بين المصدر وstaging وfact.

## 6. ما يبقى خارج dbt

- authentication وRBAC وauthorization.
- approval transitions وتغيير حالات workflow.
- إنشاء أو تعديل BudgetLine وExpense وJournalEntry.
- تنفيذ تعبيرات `CalculationRule`؛ محرك Django الآمن هو المسؤول.
- إنشاء قيود consolidation داخل `public`.
