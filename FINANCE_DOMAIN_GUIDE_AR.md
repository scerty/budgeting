# دليل المجال المالي وبناء نظام Budgeting

هذا الدليل يشرح أهم المصطلحات المالية والبرمجية اللازمة لبناء نظام تخطيط وميزانيات وتحليل مالي. الهدف ليس تعليم المحاسبة كاملة، بل بناء vocabulary مشترك يربط العمل المالي بالجداول والـ APIs والتقارير.

> ملاحظة: القواعد المحاسبية تختلف حسب الدولة والشركة. هذا الدليل مرجع تصميم برمجي عام، ويجب مراجعة محاسب قانوني عند تطبيقه على دفاتر رسمية.

## 1. الصورة الكبيرة

أي نظام مالي متطور يحتوي غالبًا على أربعة أنواع من البيانات:

```text
Master Data       الهيكل المرجعي: حسابات، فروع، أقسام، عملات
Transactions      الحركات: فواتير، مصاريف، مبيعات، قيود
Plans             الخطط: ميزانيات، Forecast، سيناريوهات
Analytics         النماذج والتقارير: فعلي مقابل مخطط وانحرافات
```

في الستاك الحالي:

```text
Django / مصادر خارجية
        ↓
PostgreSQL public أو raw
        ↓
dbt staging / intermediate / marts
        ↓
PostgreSQL analytics
        ↓
Cube.js
        ↓
Angular / Power BI
```

## 2. مفاهيم محاسبية أساسية

### الشركة والكيان القانوني

**Legal Entity** هو كيان قانوني مستقل يملك حسابات ودفاتر وقد يرفع تقارير منفصلة. الشركة الأم قد تحتوي عدة كيانات قانونية.

**Organization** في البرمجيات قد تعني مساحة العميل أو الشركة داخل النظام. ليست دائمًا مساوية لكيان قانوني واحد.

### الإيراد Revenue

المبلغ الناتج عن بيع منتج أو خدمة. الإيراد ليس بالضرورة مساويًا للمبلغ المقبوض نقدًا؛ قد يكون البيع آجلًا.

### المصروف Expense

تكلفة استهلاك خدمة أو مورد أو نشاط. في نموذجنا الحالي، `Expense` يمثل حدث مصروف مرتبط بقسم وتاريخ ومبلغ.

### التكلفة Cost

قيمة الموارد المستخدمة. قد تكون تكلفة مباشرة مرتبطة بمنتج، أو غير مباشرة تحتاج إلى توزيع على فروع أو أقسام.

### الأصل Asset

شيء تملكه الشركة وله منفعة مستقبلية، مثل النقد والمخزون والمعدات.

### الالتزام Liability

مبلغ أو واجب على الشركة، مثل قرض أو فاتورة مستحقة للمورد.

### حقوق الملكية Equity

الحق المتبقي للمالكين بعد طرح الالتزامات من الأصول.

```text
Assets = Liabilities + Equity
```

### الربح Profit

```text
Profit = Revenue - Expenses
```

وقد نحتاج أنواعًا متعددة:

- **Gross Profit**: الربح الإجمالي بعد تكلفة المبيعات.
- **Operating Profit**: الربح التشغيلي بعد مصاريف التشغيل.
- **Net Profit**: الربح الصافي بعد بقية المصاريف والضرائب والفوائد.

### التدفق النقدي Cash Flow

حركة النقد الداخل والخارج. الربح لا يساوي دائمًا التدفق النقدي بسبب المبيعات الآجلة والمصاريف المستحقة والإهلاك.

## 3. الحسابات والهيكل المالي

### دليل الحسابات Chart of Accounts

قائمة موحدة لكل الحسابات المالية المستخدمة في القيود والتقارير.

أمثلة:

```text
1000 Cash
1100 Accounts Receivable
4000 Sales Revenue
5000 Salaries Expense
5100 Rent Expense
5200 Marketing Expense
```

جدول مقترح:

```text
chart_of_accounts
- id
- organization_id
- code
- name
- account_type       asset/liability/equity/revenue/expense
- parent_id
- is_active
```

### الحساب الأب والفرعي

يمكن أن يكون الحساب هرميًا:

```text
5000 Operating Expenses
  5100 Salaries
  5200 Rent
  5300 Marketing
```

`parent_id` يسمح بالتجميع الهرمي دون تكرار الحسابات.

### مركز التكلفة Cost Center

وحدة نريد قياس تكلفتها، مثل قسم أو فرع أو فريق.

```text
cost_centers
- id
- code
- name
- branch_id
- department_id
- manager_id
- is_active
```

### مركز الربح Profit Center

وحدة نريد قياس إيراداتها وتكاليفها وربحها، مثل فرع أو منتج أو منطقة.

### البعد Dimension

طريقة لتصنيف الرقم المالي. أمثلة:

```text
Account       ماذا حدث؟
Branch        أين حدث؟
Department    من المسؤول؟
Project       لأي مشروع؟
Customer      مع من؟
Product       ماذا بعنا؟
Period        متى حدث؟
```

## 4. الحركات المالية

### Transaction

حدث مالي مسجل، مثل مصروف أو فاتورة أو دفعة أو بيع.

كل حركة يجب أن تحمل على الأقل:

```text
transaction_id
transaction_date
amount
currency
account_id
cost_center_id
source_system
source_record_id
created_at
updated_at
```

### الرأس والتفاصيل Header / Lines

المستند المالي غالبًا يتكون من:

```text
invoice                 الرأس
invoice_lines           التفاصيل
```

الرأس يحتوي المورد والتاريخ والإجمالي، والتفاصيل تحتوي الحساب والمبلغ والضريبة لكل بند.

### القيد المزدوج Double-entry

في الأنظمة المحاسبية الرسمية، كل قيد له طرف مدين وطرف دائن، ومجموعهما متساوٍ:

```text
Total Debits = Total Credits
```

الجداول المحتملة:

```text
journal_entries
journal_entry_lines
```

ولا يكفي الاعتماد على جدول مصروف واحد إذا كان النظام سيصبح دفتر أستاذ رسميًا.

### الاستحقاق Accrual

تسجيل الإيراد أو المصروف عند حدوثه، حتى لو لم يتم استلام أو دفع النقد.

### الأساس النقدي Cash Basis

تسجيل العملية عند قبض أو دفع النقد.

يجب أن يحدد المنتج من البداية هل هو نظام تخطيط وتحليل فقط، أم دفتر محاسبي يعتمد قواعد رسمية.

## 5. الميزانية Budget

### Budget

خطة مالية مستقبلية تحدد كم نتوقع أن نصرف أو نحقق خلال فترة.

### Budget Plan

دورة أو مستند ميزانية كامل، مثل:

```text
2027 Annual Operating Budget
```

### Budget Version

نسخة من الخطة في وقت معين:

```text
Original Budget
Revised Budget
Approved Budget
Latest Forecast
```

لا يفضل الكتابة فوق النسخة المعتمدة؛ أنشئ نسخة جديدة مع سجل التغيير.

### Scenario

افتراض أو احتمال مختلف:

```text
Base Case
Best Case
Worst Case
```

### Budget Line

أصغر وحدة مالية في الميزانية. مثال:

```text
فرع عمان
قسم التسويق
حساب الإعلانات
يناير 2027
10,000 USD
```

المفتاح المنطقي المقترح:

```text
(version_id, period_id, account_id, cost_center_id, project_id)
```

### Original Budget

الخطة التي تم اعتمادها أول مرة، وتستخدم كخط أساس للمقارنة.

### Revised Budget

خطة معدلة بعد تغير الظروف أو اعتماد تغييرات رسمية.

### Encumbrance

مبلغ ملتزم به بسبب أمر شراء أو عقد، لكنه لم يتحول بعد إلى مصروف فعلي.

### Available Budget

المبلغ المتبقي المتاح للصرف:

```text
Available = Approved Budget - Actuals - Encumbrances
```

## 6. التخطيط والتنبؤ

### Forecast

أفضل تقدير محدث لما سيحدث، وقد يتغير كل شهر.

### Rolling Forecast

توقع متحرك يعيد إضافة فترة مستقبلية عند انتهاء الفترة الحالية.

### Assumption

افتراض يستخدم لحساب الميزانية، مثل نمو المبيعات أو زيادة الرواتب.

### Driver-based Planning

بناء الميزانية من محركات قابلة للقياس بدل إدخال رقم نهائي فقط.

أمثلة:

```text
عدد الموظفين × تكلفة الموظف = ميزانية الرواتب
المساحة × سعر المتر = ميزانية الإيجار
المبيعات المتوقعة × نسبة التسويق = ميزانية التسويق
```

جداول مقترحة:

```text
planning_assumptions
planning_drivers
driver_values
calculation_rules
```

### Allocation

توزيع مبلغ مشترك على فروع أو أقسام باستخدام قاعدة.

مثال:

```text
مصاريف الإدارة المركزية
→ توزع حسب عدد الموظفين في كل فرع
```

## 7. الفعلي مقابل المخطط

### Actual

القيمة التي حدثت فعليًا وسجلها النظام أو مصدر خارجي.

### Budget vs Actual

مقارنة الميزانية المعتمدة مع الفعلي.

### Variance

الفرق بين الفعلي والمخطط:

```text
Variance Amount = Actual - Budget
Variance % = (Actual - Budget) / Budget * 100
```

لكن تفسير الإشارة يعتمد على نوع الحساب:

- للمصروفات: الزيادة غالبًا سلبية.
- للإيرادات: الزيادة غالبًا إيجابية.

لذلك يجب تخزين `account_type` أو `variance_direction` وعدم تفسير الرقم آليًا دون معرفة نوع الحساب.

### Favorable / Unfavorable

- **Favorable**: انحراف مفيد للشركة.
- **Unfavorable**: انحراف غير مفيد.

### Budget Attainment

نسبة تحقيق الهدف، مثل الإيرادات الفعلية مقارنة بالمستهدف.

## 8. التقارير المالية

### Income Statement

قائمة الدخل، وتعرض:

```text
Revenue
- Cost of Sales
= Gross Profit
- Operating Expenses
= Operating Profit
```

### Balance Sheet

الميزانية العمومية:

```text
Assets
Liabilities
Equity
```

### Cash Flow Statement

قائمة التدفقات النقدية، وتقسم عادة إلى:

- تشغيلية.
- استثمارية.
- تمويلية.

### P&L

اختصار Profit and Loss، أي تقرير الأرباح والخسائر، وغالبًا يقصد به قائمة الدخل.

### Management Reporting

تقارير إدارية مرنة تختلف عن القوائم القانونية، وتركز على الفروع والأقسام والمشاريع والانحرافات.

## 9. المصطلحات الزمنية

### Fiscal Year

السنة المالية، وقد لا تبدأ في يناير.

### Fiscal Period

فترة محاسبية، غالبًا شهر أو ربع.

### Month-to-date MTD

من بداية الشهر حتى تاريخ التقرير.

### Quarter-to-date QTD

من بداية الربع حتى تاريخ التقرير.

### Year-to-date YTD

من بداية السنة المالية حتى تاريخ التقرير.

### Prior Year

الفترة المقابلة من السنة السابقة.

يجب إنشاء `dim_date` تحتوي على:

```text
date_key
date_day
calendar_year
fiscal_year
quarter
month_number
month_name
is_period_closed
```

## 10. العملات والضرائب

### Transaction Currency

عملة الحركة الأصلية.

### Reporting Currency

عملة التقارير الموحدة.

### Exchange Rate

سعر تحويل العملة في تاريخ محدد.

```text
amount_reporting = amount_transaction * exchange_rate
```

### Tax / VAT

ضريبة قد تكون منفصلة عن قيمة المصروف أو الإيراد.

جداول مقترحة:

```text
currencies
exchange_rates
tax_codes
tax_rates
```

لا تخلط بين `amount_net` و`tax_amount` و`amount_gross`.

## 11. الموردون والعملاء

```text
suppliers
customers
invoices
invoice_lines
payments
payment_allocations
```

### Accounts Payable AP

المبالغ المستحقة على الشركة للموردين.

### Accounts Receivable AR

المبالغ المستحقة للشركة من العملاء.

إذا كان المنتج Budgeting فقط، يمكن تأجيل AP وAR، لكنهما مهمان عند ربط الميزانية بالواقع المالي.

## 12. الحالات وسير العمل

### Draft

مسودة قابلة للتعديل.

### Submitted

تم إرسالها للمراجعة.

### Approved

تم اعتمادها ولا يجب تعديلها مباشرة.

### Rejected

رفضت وتحتاج تعديلًا.

### Closed

أغلقت الفترة أو الخطة ولا تقبل تغييرات عادية.

جداول مناسبة:

```text
workflow_definitions
workflow_steps
approval_requests
approval_actions
```

## 13. قاموس الجداول المقترح

### Operational schema

```text
organizations
users
roles
branches
departments
cost_centers
projects
chart_of_accounts
currencies
fiscal_years
fiscal_periods
budget_plans
budget_versions
budget_lines
planning_assumptions
allocation_rules
approval_requests
comments
attachments
audit_logs
```

### Raw schema

```text
raw_expenses
raw_invoices
raw_payments
raw_budget_imports
ingestion_runs
```

ويفضل أن يحتوي كل سجل raw على:

```text
source_system
source_entity
source_record_id
record_hash
ingested_at
source_created_at
source_updated_at
is_deleted
```

### Analytics schema

```text
dim_date
dim_account
dim_branch
dim_department
dim_cost_center
dim_project
dim_scenario
fact_budget
fact_expenses
fact_actuals
fact_allocations
budget_vs_actual
budget_variance
budget_summary
```

## 14. Grain: أهم قاعدة في التحليل

**Grain** يعني ماذا يمثل الصف الواحد.

أمثلة واضحة:

```text
fact_expenses:
صف واحد لكل مصروف فعلي

fact_budget:
صف واحد لكل نسخة + حساب + مركز تكلفة + فترة + أبعاد

budget_vs_actual:
صف واحد لكل حساب + مركز تكلفة + فترة + سيناريو
```

يجب تعريف الـ grain قبل كتابة SQL أو إنشاء dashboard. معظم أخطاء التقارير تأتي من جمع جدولين لا يملكان نفس grain.

## 15. البيانات التشغيلية مقابل التحليلية

### التشغيلية

تستخدم لإدخال وتعديل البيانات:

```text
public.finance_expense
public.budget_lines
```

تحتاج علاقات وقيود وصلاحيات وتاريخ تعديل.

### التحليلية

تستخدم للقراءة والتجميع:

```text
analytics.fact_budget
analytics.fact_expenses
analytics.budget_vs_actual
```

تحتاج أداءً، grain واضحًا، واختبارات جودة. dbt يبني هذه الطبقة.

## 16. مبادئ تصميم مهمة

1. لا تحذف سجلًا ماليًا معتمدًا؛ استخدم void أو reversal أو soft delete حسب القاعدة.
2. لا تستخدم `float` للأموال؛ استخدم `decimal/numeric`.
3. خزن العملة مع كل مبلغ.
4. لا تعتمد على اسم الحساب بدل `account_id`.
5. افصل تاريخ العملية عن تاريخ إنشائها وتاريخ اعتمادها.
6. لا تعدل النسخة المعتمدة من الميزانية مباشرة.
7. احتفظ بمصدر كل رقم ووقت استيراده.
8. عرّف grain كل fact قبل بناء التقرير.
9. اختبر uniqueness وnot-null والعلاقات المرجعية.
10. افصل صلاحية تعديل الخطة عن صلاحية اعتمادها.

## 17. ربط الدليل بالنظام الحالي

النظام الحالي يحتوي على:

```text
Branch
Department
Expense
```

والعلاقة هي:

```text
Branch
  └── Department
        └── Expense
```

والخطوة الطبيعية لتوسيع النظام:

```text
Branch / Department
        ├── Expense
        └── BudgetLine
```

ثم يبني dbt:

```text
fact_expenses
fact_budget
budget_vs_actual
```

وتقرأ Cube مؤشرات مثل:

```text
Budget Amount
Actual Amount
Variance Amount
Variance Percentage
```

## 18. قاموس سريع

| المصطلح | المعنى المختصر |
|---|---|
| Actual | القيمة التي حدثت فعليًا |
| Budget | الخطة المالية المستقبلية |
| Forecast | أفضل تقدير محدث للمستقبل |
| Variance | الفرق بين الفعلي والمخطط |
| Cost Center | وحدة قياس التكلفة والمسؤولية |
| Profit Center | وحدة قياس الإيراد والتكلفة والربح |
| Account | بند مالي في دليل الحسابات |
| Dimension | طريقة تصنيف الرقم المالي |
| Fact | جدول أحداث أو أرقام قابلة للجمع |
| Dimension Table | جدول وصف وتصنيف |
| Grain | معنى الصف الواحد في الجدول |
| Accrual | تسجيل عند حدوث العملية لا عند الدفع فقط |
| Encumbrance | التزام مستقبلي لم يتحول إلى مصروف |
| Allocation | توزيع مبلغ مشترك باستخدام قاعدة |
| MTD | من بداية الشهر حتى الآن |
| QTD | من بداية الربع حتى الآن |
| YTD | من بداية السنة حتى الآن |
| P&L | الأرباح والخسائر |
| AP | مبالغ مستحقة للموردين |
| AR | مبالغ مستحقة من العملاء |
| GL | دفتر الأستاذ العام |
| ETL/ELT | استخراج وتحميل وتحويل البيانات |
| dbt | أداة بناء واختبار النماذج التحليلية |
| Semantic Layer | طبقة توحد تعريف المقاييس للتطبيقات والتقارير |

## 19. ترتيب بناء المنتج

### المرحلة الأولى: Budgeting أساسي

```text
organizations
branches
 departments
chart_of_accounts
fiscal_periods
budget_plans
budget_versions
budget_lines
```

### المرحلة الثانية: الحوكمة

```text
users
roles
approval_requests
audit_logs
comments
attachments
```

### المرحلة الثالثة: التخطيط المتقدم

```text
scenarios
planning_assumptions
planning_drivers
allocation_rules
forecast_versions
```

### المرحلة الرابعة: التحليل

```text
fact_budget
fact_actuals
budget_vs_actual
variance marts
Cube measures and dimensions
```

### المرحلة الخامسة: التكاملات

```text
CSV / Excel imports
ERP adapters
API ingestion
scheduled refresh
reconciliation reports
```

## 20. أسئلة يجب حسمها قبل البرمجة

1. هل النظام Budgeting فقط أم Accounting كامل؟
2. هل يدعم شركة واحدة أم عدة شركات؟
3. هل الميزانية شهرية أم يومية أيضًا؟
4. هل توجد عدة عملات؟
5. هل السنة المالية تبدأ من يناير؟
6. هل يوجد اعتماد متعدد المراحل؟
7. هل يمكن تعديل الميزانية بعد اعتمادها؟
8. هل نحتاج فعليًا من ERP أم من جدول المصاريف الحالي فقط؟
9. هل الميزانية حسب الحساب والقسم والفرع أم حسب أبعاد إضافية؟
10. ما تعريف الانحراف الإيجابي لكل نوع حساب؟

هذه الإجابات تحدد الجداول النهائية أكثر من اختيار Django أو dbt أو Cube.
