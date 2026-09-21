# تصميم دليل الحسابات لمجموعة قابضة متعددة الشركات والدول

## الغرض من الوثيقة

هذه الوثيقة تشرح كيف نصمم **Chart of Accounts - COA** لمجموعة قابضة تملك أو تسيطر على عدة شركات فرعية في دول مختلفة، مع اختلاف العملات والقوانين ونماذج الأعمال.

الهدف هو بناء تصميم يستطيع:

- تشغيل كل شركة وفق متطلباتها المحلية.
- توحيد التقارير على مستوى المجموعة.
- دعم شركات خدمات وتجارة وتصنيع وعقار وتقنية وغيرها.
- فصل الحساب عن الشركة والبلد والفرع ومركز التكلفة.
- دعم التحويل بين الحسابات المحلية وحسابات المجموعة.
- معالجة العملات الأجنبية والضرائب والفروقات المحاسبية.
- الاحتفاظ بتفاصيل الشركة المحلية دون إفساد التقارير الموحدة.

> هذه وثيقة تصميم نظام وليست فتوى محاسبية أو بديلًا عن مراجعة محاسب قانوني في كل دولة.

---

## 1. المشكلة التي نريد حلها

تخيل مجموعة قابضة لديها:

```text
Holding Group
├── شركة تجارة في الأردن
├── شركة خدمات في السعودية
├── شركة تصنيع في مصر
├── شركة عقارية في الإمارات
└── شركة تقنية في بريطانيا
```

كل شركة قد تختلف في:

- العملة المحلية.
- بداية السنة المالية.
- نظام الضرائب والضريبة على القيمة المضافة.
- الحسابات القانونية المطلوبة.
- نموذج الإيراد.
- طريقة تقييم المخزون.
- طريقة تسجيل الأصول والإهلاك.
- النظام المحاسبي المحلي.
- قواعد الاعتراف بالإيراد.

مع ذلك تحتاج الإدارة إلى أسئلة موحدة:

```text
ما إجمالي الإيرادات للمجموعة؟
ما تكلفة المبيعات؟
ما المصروفات التشغيلية؟
ما الأرباح حسب الدولة؟
ما أداء كل شركة؟
ما أرصدة التعاملات بين الشركات؟
ما نتيجة المجموعة بعد التوحيد والاستبعادات؟
```

إذا صممنا COA محليًا منفصلًا دون Mapping، يصبح التوحيد يدويًا وبطيئًا وخطرًا. وإذا أجبرنا كل الشركات على حسابات متطابقة حرفيًا، قد نخالف احتياجاتها المحلية.

الحل المتوازن هو:

```text
Group Chart of Accounts
        +
Local Chart of Accounts لكل شركة
        +
Mapping versioned بين المحلي والمجموعة
        +
أبعاد مستقلة للشركة والدولة والفرع ونموذج الأعمال
```

---

## 2. المبدأ الأساسي: الحساب لا يمثل كل شيء

الحساب يجيب عن سؤال:

```text
ما طبيعة الحركة المالية؟
```

ولا يجب أن يحاول في الوقت نفسه تمثيل:

```text
من يملكها؟ أين حدثت؟ من المسؤول؟ لأي مشروع؟ بأي عملة؟
```

هذه معلومات يجب أن تأتي من أبعاد منفصلة.

### مثال سيئ

```text
5101-JO-AMM-HR-USD-SALARIES
```

هذا الكود يحاول تشفير:

- الدولة.
- الفرع.
- القسم.
- العملة.
- نوع المصروف.

وسينتج عنه تضخم هائل في عدد الحسابات وصعوبة في التغيير.

### مثال أفضل

```text
Account: 610000 Salaries Expense
Entity: Jordan Trading Co.
Branch: Amman
Department: Human Resources
Currency: JOD
Project: null
```

الحساب يظل `610000`، بينما بقية المعلومات أبعاد مستقلة.

---

## 3. المصطلحات الأساسية

### Holding Company

الشركة القابضة التي تملك حصصًا أو تسيطر على شركات أخرى. قد تكون لديها عمليات فعلية، وقد تكون مجرد شركة ملكية وتمويل وإدارة.

### Group

المجموعة الكاملة: القابضة والشركات التابعة والشركات الزميلة والكيانات التي تدخل في نطاق التقارير الموحدة.

### Legal Entity

كيان قانوني مستقل له تسجيل ودفاتر والتزامات ضريبية وتقارير قانونية خاصة به.

### Subsidiary

شركة تسيطر عليها المجموعة عادة عبر الملكية أو حقوق التصويت أو السيطرة الفعلية.

### Associate

شركة تملك المجموعة فيها تأثيرًا مهمًا دون سيطرة كاملة. قد تعالج بطريقة مختلفة في تقارير المجموعة.

### Branch

فرع تابع لكيان قانوني نفسه. ليس شركة مستقلة بالضرورة.

### Country

الدولة التي يعمل أو يسجل فيها الكيان، وتحدد قواعد قانونية وضريبية وعملة محلية.

### Reporting Entity

الكيان الذي نعد له تقريرًا. قد يكون شركة فرعية، أو القابضة، أو المجموعة الموحدة.

### Consolidation

عملية جمع بيانات الكيانات الداخلة في المجموعة مع استبعاد التعاملات والأرصدة الداخلية بينها.

### Elimination

قيد استبعاد يستخدم لإزالة أثر العمليات بين شركات المجموعة حتى لا تظهر المجموعة وكأنها حققت إيرادًا من نفسها.

### Group Account

حساب موحد تستخدمه المجموعة في التقارير الموحدة.

### Local Account

حساب موجود في دفتر شركة محلية وفق نظامها القانوني أو المحاسبي.

### Mapping

قاعدة تربط حسابًا محليًا بحساب أو أكثر في دليل المجموعة.

### Posting Account

حساب يسمح بتسجيل الحركات مباشرة.

### Header / Parent Account

حساب تجميعي لا يسمح عادة بالتسجيل المباشر، ويجمع حسابات فرعية.

---

## 4. النموذج الصحيح لدليل الحسابات

نوصي بثلاث طبقات مترابطة:

```text
Group COA
    ↓ mapping
Local COA لكل Legal Entity
    ↓ posting
Journal Entries / Transactions
```

### Group COA

يحتوي على الحد الأدنى المشترك المطلوب لتقارير المجموعة.

مثال:

```text
100000 Assets
110000 Cash and Cash Equivalents
120000 Accounts Receivable
130000 Inventory
140000 Property, Plant and Equipment
200000 Liabilities
210000 Accounts Payable
220000 Loans
300000 Equity
400000 Revenue
500000 Cost of Sales
600000 Operating Expenses
700000 Other Income and Expenses
800000 Taxes
```

### Local COA

كل شركة يمكن أن تملك حسابات أكثر تفصيلًا:

```text
610101 Salaries - Sales Team
610102 Salaries - Operations Team
610103 Salaries - Administration Team
```

وقد تربط هذه الحسابات كلها بحساب المجموعة:

```text
Group Account: 610000 Salaries Expense
```

### Posting Layer

الحركات تسجل على الحساب المحلي أو على الحساب المشترك حسب سياسة النظام، لكن يجب أن يصل كل قيد في النهاية إلى Group Account واضح.

---

## 5. هل نستخدم COA واحدًا أم COA لكل شركة؟

### الخيار 1: دليل مجموعة واحد فقط

كل الشركات تستخدم نفس الحسابات والأكواد.

**المزايا:**

- توحيد سهل.
- تقارير موحدة مباشرة.
- Mapping قليل.

**المخاطر:**

- قد لا يناسب القانون المحلي.
- قد لا يناسب نموذج الأعمال.
- يفرض تفاصيل غير مفيدة على بعض الشركات.
- يصعب التعامل مع اختلافات الضرائب والدفاتر القانونية.

### الخيار 2: دليل محلي مستقل لكل شركة

كل شركة تصمم COA الخاص بها دون معيار مركزي.

**المزايا:**

- مرونة محلية عالية.
- يناسب الأنظمة الموجودة أصلًا.

**المخاطر:**

- توحيد معقد.
- اختلاف تعريف الإيراد والمصروف.
- Mapping يدوي متكرر.
- صعوبة المقارنة بين الشركات.

### الخيار 3: النموذج الهجين الموصى به

```text
Group COA موحد
+ Local COA لكل شركة
+ Mapping مضبوط بالإصدارات
```

هذا هو الخيار الأنسب للمجموعة متعددة الدول ونماذج الأعمال.

---

## 6. شكل Group Chart of Accounts

### أنواع الحسابات الرئيسية

| النوع | المعنى | أمثلة |
|---|---|---|
| Asset | أصل تملكه الشركة | نقد، مخزون، معدات |
| Liability | التزام على الشركة | موردون، قروض، ضرائب مستحقة |
| Equity | حقوق المالكين | رأس المال، الأرباح المحتجزة |
| Revenue | إيراد | مبيعات، اشتراكات، إيجارات |
| Cost of Sales | تكلفة مباشرة للإيراد | تكلفة بضاعة، مواد، عمالة مباشرة |
| Operating Expense | مصروف تشغيلي | رواتب إدارية، تسويق، إيجار |
| Other Income | دخل خارج النشاط الرئيسي | أرباح بيع أصل، فوائد دائنة |
| Other Expense | مصروف خارج النشاط الرئيسي | فوائد، خسائر صرف |
| Tax | ضرائب | ضريبة دخل، ضريبة مؤجلة |
|

### ترقيم مقترح

```text
1xxxxx Assets
2xxxxx Liabilities
3xxxxx Equity
4xxxxx Revenue
5xxxxx Cost of Sales
6xxxxx Operating Expenses
7xxxxx Other Income / Other Expenses
8xxxxx Taxes
9xxxxx Statistical / Memorandum Accounts
```

هذه مجرد سياسة ترقيم، وليست قاعدة محاسبية إلزامية. المهم ثبات المعنى والحوكمة.

### مثال هرمي

```text
400000 Revenue
├── 410000 Product Revenue
│   ├── 411000 Hardware Revenue
│   └── 412000 Software Revenue
├── 420000 Service Revenue
│   ├── 421000 Consulting Revenue
│   └── 422000 Support Revenue
└── 430000 Rental Revenue
```

---

## 7. لا تجعل نموذج الأعمال يلوث الحسابات

المجموعة قد تضم نماذج أعمال مختلفة:

### شركة تجارة

تحتاج غالبًا إلى:

```text
Product Revenue
Cost of Inventory Sold
Inventory
Purchase Returns
Freight In
Warehouse Costs
```

### شركة خدمات

تحتاج غالبًا إلى:

```text
Consulting Revenue
Subscription Revenue
Professional Salaries
Billable Hours
Unbilled Revenue
Contract Costs
```

### شركة تصنيع

تحتاج غالبًا إلى:

```text
Raw Materials
Work in Progress
Finished Goods
Direct Labor
Manufacturing Overhead
Production Variance
```

### شركة عقارية

تحتاج غالبًا إلى:

```text
Property Held for Development
Investment Property
Rental Revenue
Tenant Receivables
Property Management Costs
Construction in Progress
```

### شركة تقنية أو SaaS

تحتاج غالبًا إلى:

```text
Subscription Revenue
Usage Revenue
Deferred Revenue
Cloud Hosting Costs
Capitalized Development
Customer Acquisition Costs
```

### شركة قابضة

تحتاج غالبًا إلى:

```text
Investment in Subsidiaries
Dividend Income
Management Fees
Intercompany Loans
Interest Income
Acquisition Costs
Goodwill
```

الحل ليس إنشاء Account لكل شركة ولكل نشاط داخل كل كود. الحل هو:

```text
Group Accounts مشتركة عند الحاجة
+ Accounts فرعية خاصة بالنشاط
+ Business Model dimension
+ Product / Service dimension
+ Entity وCost Center dimensions
```

---

## 8. الحسابات والأبعاد

### ما يبقى في Account

ضع في الحساب ما يحدد الطبيعة المحاسبية:

```text
Salaries Expense
Rent Expense
Product Revenue
Trade Receivables
Inventory
```

### ما يصبح Dimension

```text
Legal Entity
Country
Branch
Department
Cost Center
Profit Center
Project
Customer
Supplier
Product
Channel
Business Model
Scenario
Currency
Fiscal Period
```

### مثال قيد غني بالأبعاد

```text
Account: 610000 Salaries Expense
Entity: Saudi Services Co.
Country: Saudi Arabia
Branch: Riyadh
Department: Delivery
Cost Center: CC-DEL-001
Project: Client Project 44
Currency: SAR
Amount: 250,000
```

يمكن لاحقًا تجميعه حسب الحساب أو الدولة أو المشروع دون إنشاء حساب جديد لكل احتمال.

---

## 9. نموذج بيانات Group COA

### group_accounts

```text
id
code
name
name_localized
account_type
normal_balance
parent_id
level
is_posting_allowed
is_consolidation_account
requires_intercompany
requires_cost_center
requires_project
is_active
valid_from
valid_to
```

### معنى أهم الحقول

- `account_type`: نوع الحساب.
- `normal_balance`: مدين أو دائن.
- `parent_id`: الحساب الأب.
- `level`: مستوى الحساب في الشجرة.
- `is_posting_allowed`: هل يقبل حركات؟
- `is_consolidation_account`: هل يستخدم في التوحيد؟
- `requires_intercompany`: هل يحتاج طرفًا داخليًا؟
- `requires_cost_center`: هل يجب تحديد مركز تكلفة؟
- `valid_from` و`valid_to`: تاريخ صلاحية الحساب.

### entity_accounts

يربط الحساب المحلي بالكيان القانوني:

```text
id
entity_id
local_code
local_name
local_account_type
currency_policy
is_posting_allowed
is_active
```

### account_mappings

```text
id
entity_id
local_account_id
group_account_id
mapping_type
mapping_version_id
valid_from
valid_to
confidence
review_status
reviewed_by
```

`mapping_type` يمكن أن يكون:

```text
one_to_one
many_to_one
one_to_many
manual_adjustment
unmapped
```

---

## 10. Mapping بين المحلي والمجموعة

### One-to-one

```text
Local 6101 Salaries
→ Group 610000 Salaries Expense
```

### Many-to-one

```text
Local 6101 Sales Salaries
Local 6102 Operations Salaries
Local 6103 Admin Salaries
→ Group 610000 Salaries Expense
```

هذا شائع ومفيد؛ يحافظ على التفاصيل المحلية ويعطي المجموعة رقمًا موحدًا.

### One-to-many

قد يحدث عندما يحتوي الحساب المحلي على مكونات يجب فصلها في المجموعة:

```text
Local 7000 General Costs
→ Group 610000 Salaries Expense
→ Group 620000 Rent Expense
→ Group 630000 Utilities Expense
```

هنا لا يكفي Mapping ثابت؛ تحتاج إلى:

- مصدر تفاصيل إضافي.
- قاعدة توزيع.
- قيد إعادة تصنيف.
- أو إبقاء الحساب في مستوى أعلى مؤقتًا.

لا توزع المبلغ اعتباطيًا فقط لجعل التقرير يبدو مفصلًا.

### Mapping غير مكتمل

يجب أن يكون للحساب حالة واضحة:

```text
mapped
pending_review
unmapped
not_applicable
blocked
```

لا تسمح بنشر تقرير موحد وكأن كل الحسابات mapped إذا كانت هناك أرصدة مهمة غير مصنفة.

---

## 11. إصدارات الـ Mapping

الـ Mapping ليس ثابتًا إلى الأبد.

مثال:

```text
Mapping Version 1: 2026-01-01 إلى 2026-06-30
Mapping Version 2: 2026-07-01 إلى الآن
```

تحتاج إلى النسخ عندما:

- يتغير دليل حسابات شركة.
- تعيد المجموعة تعريف بند في التقرير.
- تستحوذ المجموعة على شركة جديدة.
- يتغير معيار أو سياسة الاعتراف بالإيراد.
- تنقسم شركة أو تندمج.

الجداول المقترحة:

```text
mapping_versions
mapping_rules
mapping_rule_conditions
mapping_review_actions
```

يجب أن يكون تاريخ الحركة هو الذي يحدد أي Mapping ينطبق عليها، لا آخر Mapping تم حفظه.

---

## 12. الشركات والدول والعملات

### legal_entities

```text
id
organization_id
code
legal_name
country_id
functional_currency_id
reporting_currency_id
fiscal_calendar_id
local_gaap
consolidation_method
parent_entity_id
ownership_percentage
control_percentage
is_active
```

### Functional Currency

العملة الأساسية التي تعمل بها الشركة وتقيس بها نتائجها.

### Presentation / Reporting Currency

العملة التي تظهر بها تقارير المجموعة، مثل USD أو EUR.

### Transaction Currency

العملة الأصلية للحركة.

يجب عدم افتراض أن العملات الثلاث واحدة.

### مثال

```text
Company: UK Tech Ltd
Transaction currency: USD
Functional currency: GBP
Group reporting currency: USD
```

يجب الاحتفاظ بالمبلغ الأصلي وسعر الصرف والمبلغ الوظيفي ومبلغ التقرير عند الحاجة:

```text
amount_transaction
transaction_currency
exchange_rate
amount_functional
functional_currency
amount_reporting
reporting_currency
```

---

## 13. فروقات العملة

قد تظهر فروقات العملة بسبب:

- تسجيل الحركة بسعر يوم العملية.
- إعادة تقييم الرصيد بسعر نهاية الفترة.
- ترجمة نتائج شركة أجنبية إلى عملة المجموعة.
- اختلاف أسعار الصرف بين الشركات.

مصطلحات مهمة:

### Realized FX Gain/Loss

فرق تحقق عند التسوية أو الدفع.

### Unrealized FX Gain/Loss

فرق تقييم لم يتحقق نقديًا بعد.

### Translation Reserve

احتياطي فروقات ترجمة يظهر عادة في حقوق الملكية عند توحيد شركة أجنبية.

لا تخلط حسابات فروقات العملة التشغيلية مع فروقات ترجمة القوائم الموحدة.

---

## 14. الشركات التابعة والاستحواذ

عند الاستحواذ على شركة، تحتاج إلى تسجيل الفرق بين:

- القيمة العادلة للأصول والالتزامات.
- المقابل المدفوع.
- نسبة الملكية.
- الشهرة Goodwill.
- الحصص غير المسيطرة NCI.

مفاهيم مهمة:

### Goodwill

قيمة زائدة مرتبطة بالاستحواذ لا تمثل أصلًا محددًا منفصلًا، حسب القواعد المحاسبية المطبقة.

### Non-controlling Interest

حصة المالكين الآخرين في شركة تسيطر عليها المجموعة.

### Purchase Price Allocation

توزيع قيمة الاستحواذ على أصول والتزامات وقيمة متبقية.

### Consolidation Scope

يحدد هل تدخل الشركة في التقارير الموحدة، وكيف تدخل.

جداول مقترحة:

```text
acquisitions
acquisition_entities
purchase_price_allocations
ownership_periods
consolidation_scopes
```

لا يكفي تخزين `ownership_percentage` فقط؛ السيطرة قد تعتمد على حقوق تصويت أو اتفاقيات.

---

## 15. الحسابات بين الشركات Intercompany

أي تعامل بين شركتين داخل المجموعة يجب أن يسجل مع طرف مقابل:

```text
Entity A: Holding Co.
Counterparty: Subsidiary B
Account: Intercompany Receivable
Amount: 100,000
```

### أنواع شائعة

```text
Intercompany Receivable
Intercompany Payable
Intercompany Loan
Management Fee
Shared Cost Recharge
Intercompany Dividend
Intercompany Sales
Intercompany Interest
```

### لماذا نحتاج counterparty؟

لأن التوحيد يحتاج مطابقة الطرفين قبل الاستبعاد.

الجداول أو الحقول المهمة:

```text
counterparty_entity_id
intercompany_transaction_id
matching_status
elimination_status
elimination_batch_id
```

### المطابقة

```text
Company A receivable = Company B payable
```

إذا لم تتساوَ القيمتان، تظهر فروقات تحتاج تفسيرًا، مثل:

- اختلاف تاريخ التسجيل.
- اختلاف سعر الصرف.
- فاتورة غير مستلمة.
- قيد موجود في طرف واحد.
- Mapping غير صحيح.

---

## 16. قيود التوحيد Eliminations

التوحيد ليس مجرد جمع أرصدة الشركات.

الخطوات العامة:

```text
Local trial balances
        ↓
Group COA mapping
        ↓
Currency translation
        ↓
Intercompany matching
        ↓
Elimination entries
        ↓
Consolidated statements
```

### أمثلة استبعادات

- استبعاد إيراد ومصروف بين شركتين.
- استبعاد الذمم المدينة والدائنة الداخلية.
- استبعاد توزيعات الأرباح الداخلية.
- استبعاد ربح غير محقق في مخزون منقول داخليًا.
- استبعاد الاستثمار في الشركة التابعة مقابل حقوق ملكيتها في التوحيد.

### لا تعدل القيود المحلية

يجب أن تكون قيود التوحيد في طبقة منفصلة:

```text
local_ledger
adjustment_ledger
elimination_ledger
consolidated_ledger
```

حتى نستطيع معرفة:

```text
ما الذي سجلته الشركة؟
ما الذي أضافه فريق التوحيد؟
ما الذي استبعدناه؟
```

---

## 17. الشركة القابضة ليست مجرد شركة أخرى

القابضة قد تحتوي على عمليات مختلفة عن الشركات التابعة:

```text
Investment in Subsidiaries
Dividend Income
Group Management Fees
Treasury
Intercompany Financing
Acquisition Costs
Corporate Overhead
```

يجب تحديد هل مصروف القابضة:

- مصروف خاص بالقابضة.
- خدمة مقدمة للمجموعة وتحتاج إعادة تحميل.
- قيد توحيد فقط.
- مصروف استحواذ غير تشغيلي.

لا تسجل كل مصاريف القابضة على حساب عام مثل `Group Costs` دون أبعاد أو قواعد إعادة تخصيص.

---

## 18. نموذج الأعمال كأبعاد أو كحسابات؟

### استخدم الحساب عندما

الفرق له طبيعة محاسبية فعلية:

```text
Product Revenue
Service Revenue
Rental Revenue
Interest Income
```

### استخدم Dimension عندما

نريد المقارنة أو التقسيم الإداري:

```text
Retail
SaaS
Manufacturing
Real Estate
Corporate
```

### استخدم Product / Revenue Stream عندما

تحتاج تفصيلًا متعددًا يتغير باستمرار:

```text
Hardware
Subscriptions
Consulting
Rentals
Maintenance
```

### قاعدة عملية

إذا كانت الإجابة عن السؤال:

```text
ما طبيعة المبلغ؟
```

فكر في Account.

إذا كانت الإجابة عن السؤال:

```text
أين أو عند من أو لأي نشاط حدث؟
```

فكر في Dimension.

---

## 19. تصميم شجرة الحسابات

### خصائص الحساب

كل حساب يجب أن يحدد:

```text
code
name
account_type
normal_balance
parent_id
is_posting_allowed
is_control_account
requires_counterparty
requires_tax_code
requires_currency
```

### Normal Balance

الحساب له طبيعة مدينة أو دائنة:

| الحساب | الطبيعة المعتادة |
|---|---|
| Asset | مدين |
| Expense | مدين |
| Liability | دائن |
| Equity | دائن |
| Revenue | دائن |
| Contra Asset | دائن غالبًا |
| Contra Revenue | مدين غالبًا |

لا تعتمد على الإشارة وحدها لتحديد نوع الحساب؛ خزن النوع والطبيعة صراحة.

### Control Account

حساب تجميعي يجب أن تتطابق أرصدته مع نظام فرعي، مثل:

```text
Accounts Receivable Control
Inventory Control
Accounts Payable Control
Fixed Assets Control
```

### Posting Restrictions

مثال:

```text
100000 Assets           لا يقبل تسجيلًا مباشرًا
110000 Cash             يقبل تسجيلًا
111000 Bank Accounts    قد يكون تجميعيًا أو يقبل تسجيلًا حسب التصميم
```

---

## 20. الأبعاد التي يحتاجها النظام

### Entity Dimension

الشركة القانونية التي تملك الحركة.

### Branch Dimension

الموقع أو الفرع داخل الشركة.

### Department Dimension

الوحدة الإدارية.

### Cost Center Dimension

وحدة المسؤولية عن التكلفة.

### Profit Center Dimension

وحدة المسؤولية عن الربح.

### Project Dimension

مشروع أو عقد أو مبادرة.

### Product Dimension

منتج أو خدمة.

### Customer / Supplier Dimension

طرف تجاري.

### Channel Dimension

قناة بيع أو تسويق.

### Intercompany Dimension

الشركة المقابلة في تعامل داخلي.

ليس مطلوبًا أن تمتلئ كل الأبعاد في كل حركة. لكن يجب أن يحدد الحساب ما هي الأبعاد الإلزامية له.

---

## 21. قواعد التحقق Validation Rules

أمثلة لقواعد يجب تنفيذها:

```text
حساب Posting يجب أن يكون نشطًا.
حساب Parent لا يقبل قيدًا مباشرًا.
مصروفات الرواتب يجب أن تحتوي على Cost Center.
قيد Intercompany يجب أن يحتوي على Counterparty Entity.
قيد ضريبة يجب أن يحتوي على Tax Code.
حركة شركة يجب أن تستخدم عملتها الوظيفية أو تحفظ سعر تحويل صحيحًا.
الحساب المحلي يجب أن يكون mapped قبل إغلاق الفترة.
الحساب الذي تغير mapping الخاص به يجب أن يحدد تاريخ السريان.
```

هذه القواعد يجب تنفيذها في أكثر من طبقة:

```text
Django validation
Database constraints
Ingestion validation
Accounting close validation
dbt tests
```

---

## 22. الجداول التشغيلية المقترحة

### organizations

```text
id
code
name
base_reporting_currency_id
is_active
```

### legal_entities

```text
id
organization_id
code
legal_name
country_id
functional_currency_id
fiscal_calendar_id
parent_entity_id
consolidation_method
ownership_percentage
control_percentage
is_active
```

### group_accounts

```text
id
organization_id
code
name
account_type
normal_balance
parent_id
is_posting_allowed
requires_cost_center
requires_project
requires_intercompany
is_active
```

### entity_accounts

```text
id
entity_id
local_code
local_name
account_type
is_posting_allowed
is_active
```

### account_mappings

```text
id
entity_id
entity_account_id
group_account_id
mapping_version_id
mapping_type
valid_from
valid_to
review_status
```

### journal_entries

```text
id
entity_id
entry_number
entry_date
posting_date
period_id
source_system
source_record_id
status
currency_id
exchange_rate
created_by
approved_by
```

### journal_entry_lines

```text
id
journal_entry_id
local_account_id
group_account_id
branch_id
department_id
cost_center_id
profit_center_id
project_id
customer_id
supplier_id
counterparty_entity_id
debit_amount
credit_amount
currency_id
tax_code_id
description
```

### consolidation_entries

```text
id
organization_id
period_id
entry_type
source_entity_id
counterparty_entity_id
status
created_by
approved_by
```

### consolidation_entry_lines

```text
id
consolidation_entry_id
group_account_id
entity_id
debit_amount
credit_amount
currency_id
elimination_reason
```

---

## 23. التصميم التحليلي

بعد تحميل البيانات التشغيلية، يبني dbt طبقة تحليلية مثل:

```text
dim_group_account
dim_local_account
dim_legal_entity
dim_country
dim_currency
dim_date
dim_cost_center
dim_business_model
dim_intercompany_entity
```

وجداول facts:

```text
fact_journal_lines
fact_budget
fact_actuals
fact_intercompany
fact_eliminations
```

ونماذج marts:

```text
trial_balance_by_entity
trial_balance_group
income_statement_group
balance_sheet_group
cash_flow_group
intercompany_reconciliation
consolidated_pnl
entity_performance
budget_vs_actual_group
```

### Grain مقترح

```text
fact_journal_lines:
صف واحد لكل سطر قيد

fact_budget:
صف واحد لكل نسخة ميزانية + فترة + حساب مجموعة + كيان + أبعاد

fact_eliminations:
صف واحد لكل سطر قيد استبعاد

intercompany_reconciliation:
صف واحد لكل فترة + كيان + طرف مقابل + نوع حساب
```

لا تجمع أرصدة journal entries مباشرة مع budget lines قبل التأكد من تطابق grain.

---

## 24. الحسابات المحلية والتقارير المحلية

كل شركة تحتاج تقارير قانونية محلية. لذلك يجب أن يحافظ النظام على:

```text
local_account_code
local_account_name
local_tax_category
local_statutory_mapping
local_currency
local_fiscal_period
```

وفي الوقت نفسه يحتاج تقرير المجموعة إلى:

```text
group_account_code
group_account_name
group_reporting_currency
group_fiscal_period
group_policy
```

لا تستبدل الكود المحلي بكود المجموعة. احتفظ بالاثنين مع علاقة mapping واضحة.

---

## 25. الضرائب

الضريبة ليست مجرد حساب مصروف واحد.

تحتاج غالبًا إلى:

```text
tax_codes
tax_rates
tax_jurisdictions
tax_registrations
tax_account_mappings
tax_transactions
```

أمثلة:

```text
Input VAT
Output VAT
Withholding Tax
Corporate Income Tax
Deferred Tax
Payroll Tax
```

قد يستخدم نفس النشاط حسابات ضريبة مختلفة حسب الدولة. لذلك الدولة والاختصاص الضريبي أبعاد مستقلة عن الحساب العام.

---

## 26. الفترات والإغلاق

### Period Open

يسمح بالتسجيل والتعديل.

### Period Soft Close

التسجيل محدود، ويمكن لفريق المالية إكمال المراجعة.

### Period Closed

لا تقبل الحركة العادية. التعديل يحتاج قيد عكسي أو عملية إعادة فتح بصلاحية.

### Group Close

قد لا يغلق في نفس يوم إغلاق كل شركة فرعية.

جداول مقترحة:

```text
fiscal_calendars
fiscal_periods
entity_period_statuses
group_close_checklists
close_tasks
```

يجب أن تكون حالة الفترة مرتبطة بالكيان، لأن شركة قد تكون مغلقة بينما أخرى ما زالت مفتوحة.

---

## 27. الحوكمة والصلاحيات

صلاحيات مهمة:

```text
view_local_coa
edit_local_coa
edit_group_coa
create_mapping
approve_mapping
post_journal
approve_journal
run_elimination
close_entity_period
close_group_period
reopen_period
```

تغيير Group COA أو Mapping يجب أن يكون أكثر تقييدًا من تعديل اسم حساب محلي.

كل تغيير حساس يحتاج:

```text
who
when
what changed
old value
new value
reason
approval
```

---

## 28. أخطاء تصميم شائعة

### وضع الشركة داخل كود الحساب

يجعل المقارنة والتغيير صعبين. استخدم `entity_id`.

### إنشاء COA عالمي ضخم جدًا

يؤدي إلى آلاف الحسابات غير المستخدمة. استخدم Group COA مشتركًا وLocal COA متخصصة.

### استخدام اسم الحساب بدل معرفه

الأسماء قد تتغير وتتكرر. استخدم IDs ثابتة وCodes محكومة.

### تجاهل تاريخ Mapping

تغيير mapping اليوم لا يجب أن يعيد تفسير سنوات سابقة دون قرار واضح.

### جمع الشركات قبل تحويل العملة

هذا يعطي أرقامًا خاطئة. حوّل إلى عملة التقرير أولًا ثم اجمع.

### تجاهل التعاملات الداخلية

سيظهر إيراد وربح غير حقيقي للمجموعة.

### خلط الحسابات التشغيلية وقيود التوحيد

يجب الاحتفاظ بطبقات ledger منفصلة.

### جعل كل الأبعاد إلزامية

يخلق إدخالًا مرهقًا ومعلومات وهمية. اجعل الإلزام حسب الحساب ونوع الحركة.

### الاعتماد على dbt لتصحيح دفتر محاسبي

dbt مناسب للتحليل والتحويل والاختبار، لكنه ليس بديلًا عن قيود وضوابط النظام المحاسبي التشغيلي.

---

## 29. مسار عملية التوحيد

```text
1. إغلاق أو تجميد فترة كل كيان
2. فحص الحسابات غير المصنفة
3. فحص القيود غير المتوازنة
4. تحويل أرصدة العملات
5. تحميل Group Mapping
6. مطابقة Intercompany
7. إنشاء Elimination Entries
8. مراجعة فروقات التوحيد
9. بناء القوائم الموحدة
10. اعتماد Group Close
```

كل خطوة يجب أن تملك حالة ونتيجة قابلة للتتبع، لا مجرد زر ينفذ SQL صامتًا.

---

## 30. الحد الأدنى القابل للبناء MVP

إذا كان المنتج سيبدأ دون دفتر أستاذ كامل، ابدأ بـ:

```text
organizations
legal_entities
countries
currencies
fiscal_periods
group_accounts
entity_accounts
account_mappings
branches
departments
cost_centers
budget_plans
budget_versions
budget_lines
actual_expenses
```

ثم أضف:

```text
journal_entries
journal_entry_lines
intercompany_transactions
consolidation_entries
approval_workflows
audit_logs
```

### ما لا يؤجل في MVP

- تعريف الكيان القانوني.
- العملة الوظيفية.
- Group Account وLocal Account.
- تاريخ سريان Mapping.
- مصدر الحركة.
- الفترة المالية.
- `entity_id` في كل رقم مالي.

---

## 31. مثال متكامل

شركة سعودية تسجل فاتورة رواتب:

```text
Legal Entity: Saudi Services Co.
Local Account: 5110 Employee Salaries
Group Account: 610000 Salaries Expense
Country: Saudi Arabia
Functional Currency: SAR
Branch: Riyadh
Department: Delivery
Cost Center: CC-DEL-001
Fiscal Period: 2026-01
Debit: 250,000 SAR
Credit: Payroll Payable
```

شركة بريطانية تسجل فاتورة SaaS سحابية:

```text
Legal Entity: UK Tech Ltd
Local Account: 7320 Cloud Hosting
Group Account: 632000 Cloud Infrastructure Expense
Country: United Kingdom
Functional Currency: GBP
Business Model: SaaS
Fiscal Period: 2026-01
Debit: 40,000 GBP
Credit: Accounts Payable
```

في تقرير المجموعة:

- يظهر كلاهما في طبقة المصروفات التشغيلية.
- يمكن التفصيل حسب الدولة والكيان ونموذج الأعمال.
- لا يتم دمج الحسابين محليًا، بل يجمعان ضمن Group COA المناسب.
- تحول المبالغ إلى عملة التقرير بسعر السياسة المحدد.

---

## 32. أسئلة حاسمة قبل تثبيت التصميم

1. ما نطاق التوحيد: الشركات المسيطر عليها فقط أم الشركات الزميلة أيضًا؟
2. هل القوائم الموحدة وفق IFRS أم معيار آخر؟
3. ما العملة الموحدة للمجموعة؟
4. هل تختلف السنة المالية بين الشركات؟
5. هل نحتاج دفاتر محلية قانونية مستقلة؟
6. هل كل شركة تستخدم نظام ERP مختلفًا؟
7. من يملك Group COA ومن يوافق تغييراته؟
8. هل Mapping واحد للحساب أم يعتمد على نوع الحركة أو المنتج؟
9. هل نحتاج قيودًا يومية كاملة أم actuals قادمة من مصدر جاهز؟
10. كيف تتم مطابقة التعاملات الداخلية؟
11. هل نحتاج حصصًا غير مسيطرة؟
12. هل نحتاج إعادة تصنيف بين المحلي والمجموعة؟
13. كيف تعالج المجموعة فروقات العملة؟
14. ما الحسابات التي تتطلب Cost Center أو Project أو Counterparty؟
15. هل نحتفظ بتاريخ كل نسخة من COA وMapping؟

---

## الخلاصة

التصميم المتين لمجموعة قابضة متعددة الدول ليس دليل حسابات واحدًا ضخمًا، وليس أدلة محلية منفصلة بلا رابط.

التصميم الموصى به هو:

```text
Group COA موحد للتقارير
+ Local COA لكل كيان للمتطلبات القانونية والتشغيلية
+ Mapping بإصدارات وتواريخ صلاحية
+ Entity / Country / Currency كأبعاد مستقلة
+ Intercompany وElimination كطبقة واضحة
+ dbt للتحليل لا لتصحيح الدفاتر المحلية
```

القاعدة الأهم:

```text
Account يصف طبيعة الرقم.
Entity يحدد مالك الرقم.
Dimension تشرح أين ولماذا ولمن حدث.
Mapping يربط المحلي بتقرير المجموعة.
Consolidation يجمع ويستبعد ويترجم.
```
