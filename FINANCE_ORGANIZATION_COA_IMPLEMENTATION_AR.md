# التصميم الموحد للهيكل المالي والتنظيمي والتنفيذ الحالي

## 1. الغرض

هذه الوثيقة توحد بين التصميم المفاهيمي للهيكل التنظيمي ودليل الحسابات وبين نماذج Django المنفذة حاليًا ومتطلبات dbt.

هي المرجع العملي للإجابة عن الأسئلة التالية:

- ماذا يمثل كل كيان مالي؟
- أين يعيش هذا الكيان في Django؟
- ما العلاقة الصحيحة بين Organization وLegal Entity وBranch وDepartment؟
- كيف يرتبط Group COA بـ Local COA؟
- ما معنى الصف الواحد في facts وmarts؟
- ما الذي ينفذه Django، وما الذي ينفذه ingestion، وما الذي ينفذه dbt؟
- ما الذي تم تنفيذه الآن، وما الذي بقي لمرحلة دفتر الأستاذ والتوحيد؟

هذه الوثيقة لا تعد نظام Accounting قانونيًا كاملًا. التنفيذ الحالي هو foundation ناضج لمنصة Budgeting وActual Expenses والتحليل، ويمكن توسيعه لاحقًا إلى دفتر أستاذ وتوحيد كاملين.

## 2. القرار المعماري

```text
External REST / ERP / CSV / Excel
              |
              v
       Django adapters/workers
              |
              v
       PostgreSQL public/raw
              |
              v
        dbt staging
              |
              v
      dbt intermediate
              |
              v
      PostgreSQL analytics
              |
              v
       Cube / Angular / Power BI
```

المسار التشغيلي المستهدف لا يعتمد على Airbyte أو ClickHouse. الستاك القديم محفوظ للمقارنة والرجوع فقط.

### حدود الطبقات

| الطبقة | المسؤولية |
|---|---|
| Django public | master data، الميزانيات، المصروفات التشغيلية، metadata، القيود المرجعية |
| Django raw | طبقة منطقية لاستقبال السجلات الخارجية؛ `RawExpense` موجود حاليًا ضمن schema `public` وليس في schema PostgreSQL منفصلة |
| Adapter/Worker | الاتصال، pagination، authentication، retry، upsert، hash، ingestion run |
| dbt staging | تنظيف الأنواع والأكواد وتمرير المصدر دون business aggregation |
| dbt intermediate | joins، mapping الفعال، التحقق التحليلي، إعداد facts |
| dbt analytics | dimensions، facts، marts، المقاييس الموحدة |
| Cube | semantic layer للقراءة فقط |
| Angular/Power BI | العرض والفلترة واستهلاك المقاييس |

## 3. القاعدة الأساسية: لا تخلط المفاهيم

كل رقم مالي يجب أن يجيب عن أسئلة مختلفة، وكل سؤال يذهب إلى كيان أو Dimension مستقل:

```text
ما طبيعة المبلغ؟             Account / Chart of Accounts
من يملكه قانونيًا؟           Legal Entity
في أي منظمة أو مجموعة؟       Organization
في أي دولة؟                  Country / Jurisdiction
أين حدث؟                     Branch / Location
أي قسم مسؤول؟                Department
أين تحمل التكلفة؟            Cost Center
من يحقق النتيجة؟             Profit Center
لأي نشاط؟                    Business Unit
لأي مشروع أو عقد؟            Project
مع أي شركة داخلية؟           Counterparty Entity - مؤجل
بأي عملة؟                    Currency
في أي فترة؟                  Fiscal Period
لأي نسخة ميزانية؟            Budget Version
```

التصميم المرفوض:

```text
JO-AMM-HR-SAL-USD-2026
```

التصميم المنفذ:

```text
Group Account: 610000 Salaries Expense
Legal Entity: Jordan Trading Co.
Branch: Amman
Department: Human Resources
Cost Center: CC-HR-001
Currency: JOD
Fiscal Period: 2026-01
```

الحساب يجيب: **ما طبيعة الرقم؟**

الهيكل التنظيمي يجيب: **لمن وأين ومن المسؤول؟**

التوحيد يجيب لاحقًا: **من يدخل في تقرير المجموعة وكيف؟**

## 4. خريطة المفاهيم إلى نماذج Django

### 4.1 المجموعة والوقت والعملات

| المفهوم | نموذج Django | Grain | ملاحظات |
|---|---|---|---|
| Organization / Group | `Organization` | منظمة واحدة | عزل البيانات، COA المركزي، الإعدادات |
| Country / Jurisdiction | `Country` | دولة واحدة | الدولة والاختصاص والعملة الافتراضية |
| Currency | `Currency` | عملة واحدة | كود ISO، الرمز، المنازل العشرية |
| Fiscal Calendar | `FiscalCalendar` | تقويم داخل منظمة | يحدد مجموعة الفترات |
| Fiscal Period | `FiscalPeriod` | فترة داخل تقويم | تاريخ البداية والنهاية وحالة الإغلاق |

حقول `Organization` الأساسية:

```text
code
legal_name
display_name
default_reporting_currency
default_fiscal_calendar
timezone
status
```

حقول `LegalEntity` تعتمد على هذه الكيانات ولا تعيد تعريفها نصيًا.

### 4.2 الملكية والكيان القانوني

| المفهوم | نموذج Django | الغرض |
|---|---|---|
| Legal Entity | `LegalEntity` | مالك الدفاتر والحركة والعملة والفترة |
| Ownership history | `OwnershipPeriod` | الملكية والسيطرة بطريقة effective-dated |
| Parent legal entity | `LegalEntity.parent_entity` | علاقة هيكلية مباشرة، وليست بديلًا عن تاريخ الملكية |

حقول `LegalEntity` الأساسية:

```text
organization
code
legal_name
short_name
country
tax_registration_number
functional_currency
reporting_currency
fiscal_calendar
parent_entity
consolidation_method
valid_from
valid_to
status
```

لا نستنتج السيطرة من `ownership_percentage` وحده. عند الحاجة إلى تاريخ الملكية نستخدم:

```text
OwnershipPeriod
    organization
    parent_entity
    child_entity
    ownership_percentage
    control_percentage
    consolidation_method
    valid_from
    valid_to
```

قيم `consolidation_method` الحالية:

```text
full
equity
proportional
excluded
```

في التصميم المفاهيمي قد تظهر `ownership_percentage` و`control_percentage` كحقول مباشرة على `LegalEntity`. أما التنفيذ الحالي فيطبع هذه العلاقة في نموذج `OwnershipPeriod` المؤرخ؛ لذلك لا تُعد حقول الملكية المباشرة مصدر الحقيقة في النسخة الحالية. يبقى `LegalEntity.parent_entity` علاقة هيكلية مختصرة، وليس بديلًا عن سجل الملكية أو السيطرة.

### 4.3 الهيكل التشغيلي

```text
Organization
    |
    +-- LegalEntity
        +-- Branch
        +-- Department (Branch أو Entity)
        +-- CostCenter (Entity؛ وBranch/Department اختياريان)
        +-- ProfitCenter (Entity؛ وBranch/BusinessUnit اختياريان)
        +-- Project (Entity؛ وBusinessUnit اختياري)

Organization
    +-- BusinessUnit
        +-- EntityBusinessUnitAssignment
```

هذا تمثيل لنطاق الملكية وليس شجرة تبعية كاملة. `Branch` و`Department` و`CostCenter` و`ProfitCenter` و`Project` ليست كلها أبناء إلزاميين للفرع؛ العلاقات المتقاطعة أو المؤرخة تستخدم assignment models.

| المفهوم | نموذج Django | العلاقة الأساسية |
|---|---|---|
| Business Unit | `BusinessUnit` | تتبع Organization وقد تعبر أكثر من Entity |
| Entity/Business Unit scope | `EntityBusinessUnitAssignment` | علاقة effective-dated |
| Branch / Location | `Branch` | يتبع Legal Entity |
| Department | `Department` | قد يتبع Branch أو Entity مباشرة |
| Department/Entity scope | `DepartmentEntityAssignment` | قسم مشترك بين كيانات |
| Department/Branch scope | `DepartmentBranchAssignment` | قسم يخدم فروعًا متعددة |
| Cost Center | `CostCenter` | وحدة قياس وتحميل التكلفة |
| Profit Center | `ProfitCenter` | وحدة قياس الإيراد والتكلفة والنتيجة |
| Project / Contract | `Project` | بُعد مؤقت أو طويل الأجل |

حقلا `Branch.legal_entity` و`Department.legal_entity` قابلان لـ NULL حاليًا للتوافق مع البيانات القديمة. لذلك فإن التبعية القانونية إلزامية في التصميم المستهدف، لكنها تُستكمل تدريجيًا عبر backfill والتحقق أثناء الانتقال. أما السجلات الجديدة فيجب أن تربط الفرع والقسم بالكيان الصحيح.

### Department مقابل Cost Center

```text
Department = كيف نقسم الإدارة؟
Cost Center = أين نحمّل التكلفة ومن المسؤول عنها؟
```

قد يكون القسم نفسه Cost Center في شركة صغيرة، لكن لا يجب افتراض التطابق في مجموعة كبيرة.

### Business Unit مقابل Legal Entity

`BusinessUnit` يصف النشاط أو القطاع، أما `LegalEntity` فيصف كيانًا قانونيًا له دفاتر وضرائب وعملة وفترة.

لا يستخدم `BusinessUnit` بدل `LegalEntity` في القيود المالية.

## 5. دليل الحسابات COA

### 5.1 Group COA وLocal COA

التصميم المنفذ هو:

```text
Organization
    +-- GroupAccount
    |
    +-- LegalEntity
          +-- EntityAccount
                    |
                    +-- AccountMapping -> GroupAccount
```

| المفهوم | نموذج Django | النطاق |
|---|---|---|
| Group Chart of Accounts | `GroupAccount` | على مستوى Organization |
| Local Chart of Accounts | `EntityAccount` | على مستوى Legal Entity |
| Mapping release | `MappingVersion` | نسخة مؤرخة ومعتمدة |
| Local to Group rule | `AccountMapping` | قاعدة ربط قابلة للمراجعة |

### 5.2 GroupAccount

الحقول الأساسية:

```text
organization
code
name
localized_name
account_type
normal_balance
parent
level
is_posting_allowed
is_control_account
requires_cost_center
requires_project
requires_intercompany
valid_from
valid_to
is_active
```

أنواع الحسابات:

```text
asset
liability
equity
revenue
cost_of_sales
operating_expense
other_income
other_expense
tax
statistical
```

`parent` يبني الشجرة، و`is_posting_allowed` يفرق بين الحساب الأب والحساب الذي يقبل الحركة.

### 5.3 EntityAccount

يمثل الحساب المحلي للشركة:

```text
legal_entity
code
name
account_type
normal_balance
parent
is_posting_allowed
is_active
```

لا يوضع الكيان داخل كود Group Account. الأكواد المحلية قد تختلف بين الشركات، لكن Mapping يربطها بالمعنى الموحد.

### 5.4 AccountMapping

```text
EntityAccount
      |
      +-- AccountMapping -- MappingVersion -- Organization
      |
      +-- GroupAccount
```

أنواع الربط:

```text
one_to_one
many_to_one
one_to_many
manual_adjustment
unmapped
```

قواعد مهمة:

- يجب أن ينتمي الحساب المحلي والـ Group Account وMappingVersion إلى نفس Organization.
- `one_to_many` يحتاج نسب توزيع موثقة.
- لا يجوز اعتبار الحساب غير المربوط صفرًا أو إسقاطه بصمت.
- تاريخ الحركة هو الذي يحدد Mapping الفعال، لا آخر نسخة محفوظة.
- تقرير المجموعة يستخدم Mapping معتمدًا فقط.

## 6. الميزانية

الميزانية طبقة تخطيط وليست قيدًا محاسبيًا.

```text
BudgetPlan
    +-- BudgetVersion
            +-- BudgetLine
```

| النموذج | المعنى |
|---|---|
| `BudgetPlan` | دورة أو مستند خطة مثل 2027 Annual Budget |
| `BudgetVersion` | Original أو Revised أو Forecast |
| `BudgetLine` | أصغر وحدة مبلغ قابلة للمقارنة والتحليل |

### Grain الخاص بـ BudgetLine

الصف الواحد في `BudgetLine` يمثل:

```text
BudgetVersion
+ LegalEntity
+ FiscalPeriod
+ GroupAccount
+ optional EntityAccount
+ optional Branch
+ optional Department
+ optional CostCenter
+ optional ProfitCenter
+ optional BusinessUnit
+ optional Project
+ Currency
+ Amount
```

المفتاح المنطقي:

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

لا تضف Branch وهميًا إلى ميزانية على مستوى Entity فقط. كل Dimension غير فارغ يجب أن يكون حقيقيًا وتابعًا للكيان الصحيح.

حالات الميزانية:

```text
draft
submitted
approved
rejected
closed
```

لا تعدل النسخة المعتمدة مباشرة؛ أنشئ نسخة Revised أو Forecast حسب الحالة.

## 7. Ingestion والمصروفات الفعلية

### 7.1 دورة ingestion

```text
مصدر خارجي
    -> IngestionRun
    -> RawExpense أو RawJournalLine
    -> mapping/validation
    -> Expense أو JournalEntry/JournalEntryLine أو fact_expenses
```

`ImportSource` يسجل الاتصال المهيأ بالمصدر، بينما يبقى `IngestionRun` هو سجل الدفعة
والتنفيذ الفعلي. لا تخزن الأسرار داخل `configuration`؛ يحفظ `secret_ref` مرجعًا
خارجيًا لإدارة الأسرار.

### IngestionRun

يسجل دورة الاستيراد:

```text
organization
source_system
source_entity
strategy
status
external_run_id
started_at
finished_at
records_read
records_inserted
records_updated
records_skipped
records_failed
error_message
error_log
triggered_by
import_source
```

الاستراتيجيات المتاحة:

```text
cursor
snapshot
append_only
full_refresh
```

### RawExpense

يمثل سجل المصدر كما وصل قبل تطبيق mapping:

```text
ingestion_run
source_system
source_entity
source_record_id
amount
currency
expense_date
description
source_account_code
source_branch_code
source_department_code
source_cost_center_code
source_created_at
source_updated_at
ingested_at
record_hash
is_deleted
source_payload
```

المفتاح idempotent:

```text
source_system + source_entity + source_record_id
```

لا يطبق `RawExpense` أسماء الكيانات الداخلية مباشرة؛ تتم عملية الربط في adapter أو service أو dbt بحسب نوع المصدر.

### RawJournalLine

يمثل سطر GL الخام قبل تحويله إلى قيد تشغيلي أو نموذج تحليلي. يحتفظ بأكواد المصدر
والعملة والمبالغ المدينة/الدائنة وبيانات المستند والـ hash وpayload الأصلي. يفرض
النموذج أن يكون السطر مدينًا أو دائنًا فقط، وأن يكون مفتاحه idempotent:

```text
source_system + source_entity + source_record_id + source_line_id
```

### IngestionIssue و NewCodeDiscovery

`IngestionIssue` يسجل خطأ أو تحذيرًا على مستوى الصف مع رقم الصف والكود والرسالة،
بدل وضع كل التفاصيل في JSON واحد داخل الدفعة. أما `NewCodeDiscovery` فيسجل أي
حساب أو بُعد تنظيمي غير موجود في master data، مع حالة المراجعة والربط أو الإنشاء.

### Expense الحالي

`Expense` هو سجل المصروف التشغيلي/الفعلي الحالي، ويحافظ على العلاقة القديمة:

```text
Department -> Branch
Expense -> Department
```

ويضيف السياق المالي:

```text
branch
legal_entity
entity_account
group_account
cost_center
profit_center
business_unit
project
currency
currency_master
source_system
source_entity
source_record_id
record_hash
ingested_at
source_created_at
source_updated_at
is_deleted
```

وجود `currency` النصي إلى جانب `currency_master` هو توافق انتقالي مع البيانات الحالية. يجب أن يكون الكود موحدًا مع مرجع `Currency`، ويجب أن تنتقل المصادر الجديدة إلى المرجع المنظم عند اكتمال migration الخاصة بالعملة.

## 8. قواعد الاتساق المنفذة

### على مستوى قاعدة البيانات

- Unique codes ضمن النطاق المناسب مثل Organization وLegal Entity وCOA.
- نسب الملكية والسيطرة بين 0 و100.
- `valid_to >= valid_from` عندما يوجد تاريخ نهاية.
- نهاية الفترة بعد بدايتها.
- نهاية المشروع بعد بدايته عند توفر التاريخين.
- منع تكرار source key في `RawExpense` و`Expense`.
- منع تكرار BudgetLine على grain المحدد.
- منع الحساب الأب من أن يكون نفسه.
- منع Parent Entity من أن يكون الكيان نفسه.

### على مستوى Django validation

`clean()` و`full_clean()` يتحققان من قواعد لا يستطيع Foreign Key العادي التعبير عنها، مثل:

- Branch وDepartment يتبعان Legal Entity نفسه.
- Cost Center وProject يتبعان الكيان الصحيح.
- Group Account وEntity Account ينتميان إلى Organization متوافقة.
- Budget period يتبع Fiscal Calendar الخاص بالكيان.
- MappingVersion والحسابات تقع في Organization نفسها.
- العملة النصية في Expense تطابق `currency_master`.

مهم: Django لا يستدعي `full_clean()` تلقائيًا عند كل `save()`. يجب أن تستدعيه الخدمات والنماذج الإدارية وواجهات الإدخال قبل الحفظ، مع إبقاء قيود قاعدة البيانات للحالات القابلة للتعبير SQL.

## 9. نموذج الحركة المالية الموحد

الحركة الفعلية الحالية ليست Journal Entry كاملًا، لكنها تحمل الأساس المطلوب للتحليل:

```text
Expense
    source_system
    source_entity
    source_record_id
    legal_entity
    branch
    department
    entity_account
    group_account
    cost_center
    profit_center
    business_unit
    project
    expense_date
    amount
    currency
    is_deleted
```

عند بناء دفتر الأستاذ لاحقًا، يصبح النموذج الصحيح:

```text
JournalEntry
    +-- JournalEntryLine
            account
            legal_entity
            branch
            department
            cost_center
            profit_center
            project
            currency
            fiscal_period
            counterparty_entity
            debit
            credit
```

لا تستخدم `Expense` كبديل عن `JournalEntryLine` عندما يصبح النظام محاسبيًا مزدوج القيد.

## 10. متطلبات dbt المرتبطة بالنماذج الحالية

### 10.1 مصادر staging

يجب تعريف جداول Django التالية كمصادر `public`:

```text
finance_organization
finance_country
finance_currency
finance_fiscalcalendar
finance_fiscalperiod
finance_legalentity
finance_ownershipperiod
finance_businessunit
finance_entitybusinessunitassignment
finance_branch
finance_department
finance_departmententityassignment
finance_departmentbranchassignment
finance_costcenter
finance_profitcenter
finance_project
finance_groupaccount
finance_entityaccount
finance_mappingversion
finance_accountmapping
finance_accounthierarchy
finance_accounthierarchynode
finance_budgetplan
finance_budgetversion
finance_budgetline
finance_importsource
finance_ingestionrun
finance_ingestionissue
finance_newcodediscovery
finance_rawexpense
finance_rawjournalline
finance_expense
finance_exchangerate
finance_taxcode
finance_taxrate
finance_supplier
finance_customer
finance_invoice
finance_invoiceline
finance_payment
finance_paymentallocation
finance_planningassumption
finance_planningdriver
finance_drivervalue
finance_calculationrule
finance_allocationrule
finance_allocationruleline
finance_encumbrance
finance_workflowdefinition
finance_workflowstep
finance_approvalrequest
finance_approvalaction
finance_auditlog
finance_journalentry
finance_journalentryline
finance_consolidationgroup
finance_consolidationscope
finance_intercompanypair
finance_eliminationrule
finance_consolidationrun
finance_eliminationentry
finance_minorityinterestentry
finance_translationadjustment
finance_goodwillcalculation
finance_intercompanyinventoryelimination
finance_intercompanymatch
```

كل staging model يحافظ على grain المصدر ولا ينفذ aggregation.

### 10.2 نماذج staging الأساسية

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
stg_budget_plans
stg_budget_versions
stg_budget_lines
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
stg_allocation_rules
stg_allocation_rule_lines
stg_encumbrances
stg_workflow_definitions
stg_workflow_steps
stg_approval_requests
stg_approval_actions
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
```

التنظيف المسموح في staging:

- إعادة تسمية الحقول إلى `*_id` و`*_code` الواضحة.
- تحويل amount إلى numeric.
- توحيد الأكواد إلى uppercase وtrim.
- توحيد currency إلى `currency_code`.
- تمرير timestamps وhash وis_deleted.
- عدم إسقاط السجلات غير المربوطة بصمت.

### 10.3 Grain المصروف

`stg_expenses` و`int_expenses_enriched` و`fact_expenses` يجب أن تكون:

```text
صف واحد لكل:
source_system + source_entity + source_record_id
```

يحتفظ `expense_id` كمفتاح Django داخلي، لكنه ليس المفتاح العالمي للمصادر المتعددة.

### 10.4 Grain الميزانية

`fact_budget` يحافظ على صف واحد لكل `BudgetLine` وعلى grain المركب الموثق في قسم الميزانية. لا تجمع الميزانية مع actuals قبل توحيد:

```text
organization
legal_entity
period
group_account
branch
department
cost_center
project
scenario
currency
```

### 10.5 Intermediate models

```text
int_expenses_enriched
int_budget_lines_enriched
int_account_mappings_effective
int_actuals_budget_ready
int_invoices_enriched
int_payments_allocated
int_encumbrances_budget_ready
int_planning_driver_values
int_allocation_rules_effective
int_journal_entries_balanced
```

المسؤوليات:

- ربط المصروف بالأبعاد دون مضاعفة الصفوف.
- اختيار Assignment وMapping الصالحين حسب التاريخ.
- كشف الحسابات غير المربوطة.
- التحقق من توافق الكيان والحساب والفترة والعملة.
- تجهيز actual وbudget لنفس grain قبل المقارنة.

### 10.6 Dimensions

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
dim_budget_version
dim_supplier
dim_customer
dim_tax_code
dim_date
```

كل Dimension يجب أن يملك صفًا واحدًا لكل ID، وألا يعتمد على الاسم كـ primary key.

### 10.7 Facts وmarts

```text
fact_expenses
fact_budget
fact_invoices
fact_payments
fact_encumbrances
fact_planning_driver_values
budget_vs_actual
expenses_by_branch
expenses_by_month
expenses_by_branch_month
```

تبقى `fact_journal_lines` خارج MVP التحليلي الحالي إلى أن يثبت نشر دفتر الأستاذ؛ وجود staging للقيود لا يغير مصدر actuals الحالي، وهو `fact_expenses`.

Grain `budget_vs_actual` الافتراضي:

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
expense_count
```

`expenses_by_branch_month` يجب أن يضمن:

```text
صف واحد لكل branch_id + month_key
```

## 11. اختبارات dbt المطلوبة

### المفاتيح

- `not_null` و`unique` لكل Dimension primary key.
- uniqueness لمفتاح المصروف المصدر المركب.
- uniqueness لـ BudgetLine على grain الموثق.
- uniqueness لـ `branch_id + month_key` في mart الشهرية.

### العلاقات

- Expense إلى Department.
- Department إلى Branch أو assignment صالح.
- Branch وDepartment وCostCenter إلى LegalEntity الصحيح.
- EntityAccount إلى LegalEntity.
- GroupAccount إلى Organization.
- FiscalPeriod إلى FiscalCalendar الخاص بالكيان.
- كل foreign key في facts إلى Dimension مقابلة.

### الاتساق المالي

- amount غير NULL، ويفسر reversal قبل فرض الإيجابية.
- currency code موجود في `dim_currency`.
- لا تظهر `is_deleted = true` في fact الحالي.
- لا يوجد Mapping معتمد متضارب لنفس التاريخ.
- نسب one-to-many لا تتجاوز السياسة المعتمدة.
- القسمة على صفر في `variance_percentage` معرفة صراحة.
- مجموع fact يطابق staging بعد تطبيق سياسة الحذف والاستثناءات.

### Freshness وreconciliation

- freshness على `updated_at` أو `source_updated_at`.
- كل RawExpense مرتبط بـ IngestionRun.
- فشل ingestion أو dbt يمنع إعلان دورة refresh ناجحة.
- exception models تعرض الحسابات والأبعاد غير المربوطة بدل إسقاطها.

## 12. الصلاحيات وسير الموافقات

النماذج الحالية تخزن بعض المسؤولين مثل `owner`, `manager`, و`budget_owner`، وتنفذ الآن أساس سير الموافقات عبر `WorkflowDefinition` و`WorkflowStep` و`ApprovalRequest` و`ApprovalAction`، إضافة إلى `AuditLog`. أما نموذج صلاحيات البيانات التفصيلي فما يزال مؤجلًا.

النموذج المستهدف للصلاحية هو:

```text
Action Permission + Data Scope + Workflow State
```

أمثلة:

```text
Budget Editor
    يعدل BudgetLine داخل Entity محدد
    في فترة مفتوحة
    ولا يعتمد النسخة

Group Controller
    يرى كل Entities
    يعتمد Mapping
    يشغل Consolidation
    ولا يعدل القيود المحلية مباشرة
```

النماذج المؤجلة:

```text
roles
permissions
user_organization_scopes
user_entity_scopes
user_branch_scopes
approval_requests
approval_actions
audit_logs
```

الموجود فعليًا هو نماذج الموافقات والتدقيق المذكورة أعلاه؛ المؤجل هنا هو نطاقات المستخدمين المخصصة مثل `user_organization_scopes` و`user_entity_scopes` و`user_branch_scopes`.

## 13. ما تم تنفيذه فعليًا

تم تنفيذ النواة التالية في `finance.models`:

```text
Organization
Country
Currency
FiscalCalendar
FiscalPeriod
LegalEntity
OwnershipPeriod
BusinessUnit
EntityBusinessUnitAssignment
Branch
Department
DepartmentEntityAssignment
DepartmentBranchAssignment
CostCenter
ProfitCenter
Project
GroupAccount
EntityAccount
MappingVersion
AccountMapping
AccountHierarchy
AccountHierarchyNode
BudgetPlan
BudgetVersion
BudgetLine
ImportSource
IngestionRun
IngestionIssue
NewCodeDiscovery
RawExpense
RawJournalLine
Expense
ExchangeRate
TaxCode
TaxRate
Supplier
Customer
Invoice
InvoiceLine
Payment
PaymentAllocation
PlanningAssumption
PlanningDriver
DriverValue
CalculationRule
AllocationRule
AllocationRuleLine
Encumbrance
WorkflowDefinition
WorkflowStep
ApprovalRequest
ApprovalAction
AuditLog
JournalEntry
JournalEntryLine
ConsolidationGroup
ConsolidationScope
IntercompanyPair
EliminationRule
ConsolidationRun
EliminationEntry
MinorityInterestEntry
TranslationAdjustment
GoodwillCalculation
IntercompanyInventoryElimination
IntercompanyMatch
```

كما تم تنفيذ:

- Migration `0003` للنماذج الجديدة.
- Migration `0004` لنماذج المعاملات والتخطيط والحوكمة ودفتر الأستاذ.
- Migration `0005` لمصادر الاستيراد وGL الخام وأخطاء الإدخال واكتشاف الأكواد.
- Migration `0006` لهياكل COA المتوازية ونماذج التوحيد والاستبعادات والتعاملات البينية.
- Backfill للبيانات القديمة إلى Organization وLegalEntity وCurrency وCOA أولي.
- حماية Views dbt الحالية من تغييرات column type غير الآمنة.
- تسجيل النماذج في Django Admin.
- اختبارات اتساق للمصروف وBudgetLine والقيد والفاتورة والتوزيع وسعر الصرف والاستيراد وCOA والتوحيد.
- وثيقة dbt تفصيلية مستقلة.

أما تنفيذ dbt الحالي فما يزال محدودًا بالمسار التشغيلي السابق:

```text
stg_branches
stg_departments
stg_expenses
int_expenses_enriched
fact_expenses
expenses_by_branch
expenses_by_month
expenses_by_branch_month
```

لذلك فإن `stg_organizations` و`stg_legal_entities` و`stg_group_accounts` و`fact_budget` و`budget_vs_actual` وبقية النماذج المذكورة في قسم متطلبات dbt هي عقد تصميم وخطة تنفيذ، وليست نماذج dbt موجودة كلها في المستودع بعد.

## 14. الحالة الحالية للبيانات التجريبية

السياق التجريبي الحالي:

```text
Organization: DEMO
Legal Entity: DEMO-JO
Currencies: USD, JOD
Group Account: 600000 Operating Expenses
Entity Account: 600000 Operating Expenses
Mapping: MAP-2026-01
Branches: 3
Departments: 12
Expenses: 6
```

المصروفات الحالية تستخدم `USD` للحفاظ على البيانات التعليمية السابقة، مع وجود مرجع `Currency` منظم. هذا لا يعني أن العملة الوظيفية لكل شركة يجب أن تكون USD في التصميم النهائي.

## 15. ما لم ينفذ بعد

منفذ الآن في Django كطبقة تشغيلية:

```text
ConsolidationGroup
ConsolidationScope
ConsolidationRun
IntercompanyPair
EliminationRule
EliminationEntry
MinorityInterestEntry
TranslationAdjustment
GoodwillCalculation
IntercompanyInventoryElimination
IntercompanyMatch
```

أصبح `JournalEntry` و`JournalEntryLine` أساس دفتر الأستاذ التشغيلي، كما أصبحت قواعد
التوحيد والاستبعاد والمطابقة ممثلة تشغيليًا. ما يزال نشر `fact_journal_lines` و`fact_intercompany`
و`fact_eliminations` و`consolidated_financials` في dbt خارج MVP التحليلي. لا يستخدم `Expense`
بديلًا عن دفتر الأستاذ العام.

## 16. ترتيب التنفيذ التالي

1. بناء staging للمصادر المعرفة، بما فيها `stg_raw_journal_lines` و`stg_ingestion_issues`.
2. بناء staging للمنظمة والكيان والعملة والفترة والفرع والقسم.
3. بناء `stg_expenses` و`int_expenses_enriched` مع tests.
4. بناء Dimensions و`fact_expenses` على PostgreSQL analytics.
5. بناء `fact_budget` ثم `budget_vs_actual`.
6. إضافة exception models للحسابات والأبعاد غير المربوطة.
7. تحديث Cube لقراءة analytics الجديدة.
8. اختبار INSERT وUPDATE وDELETE وretry وpartial failure وfull recovery.
9. إضافة permissions وapproval workflow.
10. إضافة Journal Entries ثم Intercompany ثم Consolidation.

لا تضف incremental dbt أو scheduling قبل إثبات idempotency وupdate detection وdelete handling وbackfill وrecovery.

## 17. معايير قبول التصميم

يعد التصميم الحالي صالحًا لمرحلة foundation عندما:

- تكون كل حركة مرتبطة بـ Organization/Legal Entity أو تظهر كـ exception.
- لا يوضع Branch أو Currency أو Business Unit داخل كود الحساب.
- يمكن ربط Local Account بـ Group Account عبر Mapping مؤرخ.
- لا تتكرر المصروفات عند إعادة ingestion.
- يبقى BudgetLine على grain واضح وغير مكرر.
- يمكن لـ dbt بناء facts من public/raw إلى analytics.
- تمر اختبارات not-null وunique وrelationships وgrain.
- يفشل refresh عند فشل ingestion أو dbt.
- تكون القيود المؤجلة موثقة ولا يتم إخفاؤها داخل نماذج مبسطة.

## الخلاصة

التصميم الموحد هو:

```text
Organization
    +-- LegalEntity / OwnershipPeriod
    +-- GroupAccount
    +-- BusinessUnit
    +-- FiscalCalendar / Currency

LegalEntity
    +-- Branch / Department / CostCenter / ProfitCenter / Project
    +-- EntityAccount
    +-- BudgetLine
    +-- Expense

EntityAccount
    +-- AccountMapping -> GroupAccount

RawExpense
    +-- IngestionRun
    +-- source metadata

Django public/raw
    -> dbt staging
    -> dbt intermediate
    -> dbt facts/dimensions/marts
```

القاعدة الذهبية:

```text
Chart of Accounts يصف طبيعة الرقم.
Organization Structure يصف الملكية والتشغيل والمسؤولية.
Effective dating يحفظ معنى التاريخ.
Ingestion metadata يحفظ مصدر الرقم.
dbt يوحد التحليل ولا يصحح دفترًا محاسبيًا غير موجود.
Consolidation يجمع ويترجم ويستبعد في طبقة مستقلة عند بنائه.
```
