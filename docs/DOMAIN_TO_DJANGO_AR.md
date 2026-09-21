# خريطة المجال إلى Django

Django يملك الجداول في PostgreSQL `public`. هذه الجداول هي مصدر الحقيقة للبيانات التشغيلية والإعدادات والقيود وسير العمل.

## 1. التنظيم والهيكل المالي

| المجال | Django models | جداول المصدر | الغرض |
|---|---|---|---|
| المنظمة والكيان | `Organization`, `LegalEntity`, `OwnershipPeriod` | `finance_organization`, `finance_legalentity`, `finance_ownershipperiod` | حدود العميل والكيانات والملكية الزمنية |
| الزمن والعملة | `Country`, `Currency`, `FiscalCalendar`, `FiscalPeriod`, `ExchangeRate` | `finance_country`, `finance_currency`, `finance_fiscalcalendar`, `finance_fiscalperiod`, `finance_exchangerate` | التقويم والعملات والتحويل |
| الهيكل التشغيلي | `BusinessUnit`, `Branch`, `Department`, `CostCenter`, `ProfitCenter`, `Project` | جداول `finance_*` المطابقة | أبعاد المسؤولية والموقع والمشروع |
| assignments | `EntityBusinessUnitAssignment`, `DepartmentEntityAssignment`, `DepartmentBranchAssignment` | جداول `finance_*assignment` | نطاق الصلاحية الفعال زمنيًا |

الملفات المالكة: [organization.py](../django/finance/models/organization.py).

## 2. دليل الحسابات والربط

| المفهوم | Django model | جدول | قرار الملكية |
|---|---|---|---|
| حساب المجموعة | `GroupAccount` | `finance_groupaccount` | Django master data |
| الحساب المحلي | `EntityAccount` | `finance_entityaccount` | Django master data |
| نسخة الربط | `MappingVersion` | `finance_mappingversion` | Django يثبت النسخة والتاريخ |
| ربط الحسابات | `AccountMapping` | `finance_accountmapping` | Django يثبت النوع والنسب والمراجعة |
| هيكل التقرير | `AccountHierarchy`, `AccountHierarchyNode` | `finance_accounthierarchy`, `finance_accounthierarchynode` | Django configuration للتقرير |

الملفات المالكة: [organization.py](../django/finance/models/organization.py) و[reporting.py](../django/finance/models/reporting.py).

## 3. الحركات الفعلية

| المفهوم | Django model | جدول | الحالة |
|---|---|---|---|
| مصروف فعلي | `Expense` | `finance_expense` | مصدر المسار المنفذ حاليًا |
| مصدر استيراد | `ImportSource`, `IngestionRun` | `finance_importsource`, `finance_ingestionrun` | مصدر orchestration وaudit |
| landing خام | `RawExpense`, `RawJournalLine` | `finance_rawexpense`, `finance_rawjournalline` | تحفظ raw ولا تطبق mapping |
| AP/AR | `Supplier`, `Customer`, `Invoice`, `InvoiceLine` | جداول `finance_*` المطابقة | تشغيلية، وتحليلها لاحقًا في dbt |
| النقد | `Payment`, `PaymentAllocation` | `finance_payment`, `finance_paymentallocation` | تشغيلية، ولا تخلط مع invoice |
| الضرائب والعملات | `TaxCode`, `TaxRate`, `ExchangeRate` | جداول `finance_*` المطابقة | إعدادات وحركات مساعدة |
| دفتر الأستاذ | `JournalEntry`, `JournalEntryLine` | `finance_journalentry`, `finance_journalentryline` | Django يفرض التوازن والنشر |

الملفات المالكة: [operations.py](../django/finance/models/operations.py)، [ingestion.py](../django/finance/models/ingestion.py)، و[ledger.py](../django/finance/models/ledger.py).

## 4. الميزانية والتخطيط

| المفهوم | Django model | جدول | دور Django |
|---|---|---|---|
| خطة الميزانية | `BudgetPlan` | `finance_budgetplan` | تعريف الخطة ومالكها وحالتها |
| نسخة الميزانية | `BudgetVersion` | `finance_budgetversion` | versioning وحالة الاعتماد |
| سطر الميزانية | `BudgetLine` | `finance_budgetline` | إدخال مالي عند grain الأبعاد |
| السيناريو | `Scenario`, `ScenarioVersion` | `finance_scenario`, `finance_scenarioversion` | حالات ونسخ قابلة للقفل |
| المزج | `ScenarioBlend` | `finance_scenarioblend` | تعريف النطاق والأولوية |
| drivers | `PlanningAssumption`, `PlanningDriver`, `DriverValue` | جداول `finance_*` المطابقة | مدخلات التخطيط |
| القواعد | `CalculationRule`, `CalculationRuleDependency` | جداول `finance_*` المطابقة | قواعد آمنة وgraph تبعيات |
| التشغيل والنتائج | `CalculationRun`, `PlanningFact` | `finance_calculationrun`, `finance_planningfact` | lineage ونتائج التنفيذ قبل نشرها في dbt |
| الالتزامات | `Encumbrance` | `finance_encumbrance` | التزام غير محول إلى actual |

الملفات المالكة: [planning.py](../django/finance/models/planning.py) و[planning_rules.py](../django/finance/models/planning_rules.py).

## 5. التحكم والتقارير والتوحيد

| المجال | Django models | قرار الملكية |
|---|---|---|
| RBAC | `Role`, `UserProfile`, `UserOrgScope` | Django فقط؛ dbt لا يفرض authorization |
| workflow | `WorkflowDefinition`, `WorkflowStep`, `ApprovalRequest`, `ApprovalAction` | Django يملك الحالة والأحداث |
| submissions | `PlanningSubmission` | Django يملك التسليم والاعتماد |
| التقرير | `ReportGroup`, `ReportTemplate`, `ReportColumnModel`, `ReportColumnModelItem`, `ReportColumn` | Django يملك layout والإعدادات |
| snapshot | `ReportRunSnapshot` | Django يملك artifact وmetadata، وليس fact ماليًا |
| التوحيد | `ConsolidationGroup`, `ConsolidationScope`, `IntercompanyPair`, `EliminationRule`, `ConsolidationRun` | Django يملك الإعداد والتشغيل |
| مخرجات التوحيد | `EliminationEntry`, `MinorityInterestEntry`, `TranslationAdjustment`, `GoodwillCalculation`, `IntercompanyInventoryElimination`, `IntercompanyMatch` | مصدر محتمل لـ dbt بعد اعتماد دورة التوحيد |

الملفات المالكة: [access.py](../django/finance/models/access.py)، [workflow.py](../django/finance/models/workflow.py)، [reporting.py](../django/finance/models/reporting.py)، و[consolidation.py](../django/finance/models/consolidation.py).

## قاعدة التغيير

إذا كان التغيير يجيب عن أحد الأسئلة التالية فهو Django غالبًا:

- من يستطيع التعديل أو الاعتماد؟
- ما الحالة الحالية للوثيقة؟
- ما القاعدة أو النسخة التي اختارها المستخدم؟
- كيف نمنع سجلًا غير صالح داخل transaction؟

إذا كان التغيير يجيب عن هذه الأسئلة فهو dbt غالبًا:

- كيف نجمع ونقارن وننشر؟
- ما هو الـ fact أو dimension القابل لإعادة البناء؟
- ما الاستثناءات الناتجة عن عدم الربط أو عدم الاتساق؟
