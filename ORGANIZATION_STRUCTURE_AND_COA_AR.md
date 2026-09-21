# تصميم الهيكل التنظيمي وعلاقته بـ Chart of Accounts

## الغرض

هذه الوثيقة تشرح مفهوم **Organization Structure** في نظام مالي وBudgeting متعدد الشركات، وكيف يؤثر في:

- نموذج البيانات.
- الصلاحيات.
- إدخال الميزانيات.
- تسجيل الحركات المالية.
- التقارير التشغيلية والتحليلية.
- التوحيد المالي.
- علاقته بدليل الحسابات Chart of Accounts.

الهدف هو منع خلط مفاهيم مختلفة داخل جدول واحد أو داخل كود حساب واحد.

> الهيكل التنظيمي يصف من يملك ويدير النشاط وأين يقع. دليل الحسابات يصف طبيعة المبلغ ماليًا. قد يرتبطان في الحركة المالية، لكنهما ليسا الشيء نفسه.

---

## 1. الفكرة الأساسية

أي رقم مالي في النظام يحتاج عادة إلى إجابات عن أسئلة مختلفة:

```text
ما طبيعة المبلغ؟             Account / Chart of Accounts
أي كيان قانوني يملكه؟       Legal Entity
في أي دولة؟                  Country / Jurisdiction
في أي فرع أو موقع؟           Branch / Location
أي قسم مسؤول عنه؟            Department
من يتحمل التكلفة؟            Cost Center
أي نشاط أو قطاع؟             Business Unit / Business Model
لأي مشروع أو عميل؟           Project / Customer
هل الطرف شركة من المجموعة؟  Intercompany Entity
في أي فترة؟                  Fiscal Period
```

الخطأ هو وضع كل الإجابات في كود واحد مثل:

```text
JO-AMM-HR-SAL-USD-2026
```

والتصميم الأفضل هو تخزين كل مفهوم في كيان أو Dimension مناسب:

```text
Account: 610000 Salaries Expense
Legal Entity: Jordan Trading Co.
Country: Jordan
Branch: Amman
Department: Human Resources
Cost Center: CC-HR-001
Currency: JOD
Fiscal Period: 2026-01
```

---

## 2. ما هو Organization Structure؟

هو النموذج الذي يصف شكل المؤسسة وعلاقات الملكية والإدارة والتشغيل داخلها.

قد يتكون من مستويات مختلفة:

```text
Group / Organization
├── Holding Company
├── Legal Entity
│   ├── Business Unit
│   ├── Branch / Location
│   ├── Department
│   ├── Cost Center
│   └── Profit Center
├── Project
└── Team / User Scope
```

لكن هذه المستويات ليست كلها من النوع نفسه.

بعضها يصف **الملكية القانونية**، وبعضها يصف **الإدارة**، وبعضها يصف **مكان التشغيل**، وبعضها يصف **طريقة التحليل**.

لذلك لا يجب وضعها جميعًا في شجرة واحدة إلا إذا كان واضحًا لأي غرض تستخدم تلك الشجرة.

---

## 3. أهم تمييز: الملكية، القانون، الإدارة، والتحليل

### 3.1 Ownership Structure

يجيب عن:

```text
من يملك من؟
```

مثال:

```text
Holding Group
├── تملك 100% من Jordan Trading Co.
├── تملك 75% من Saudi Services Co.
└── تملك 40% من Egypt Manufacturing Co.
```

هذا الهيكل مهم للاستحواذ والتوحيد والحصص غير المسيطرة.

### 3.2 Legal Structure

يجيب عن:

```text
ما الكيانات القانونية المستقلة؟
```

كل Legal Entity قد يكون له:

- تسجيل قانوني مستقل.
- رقم ضريبي.
- دفاتر وحسابات.
- عملة وظيفية.
- سنة مالية.
- تقارير قانونية.

### 3.3 Management Structure

يجيب عن:

```text
من يدير من؟
```

قد يكون مدير إقليمي مسؤولًا عن أقسام موجودة في عدة شركات قانونية. لذلك الهيكل الإداري لا يساوي دائمًا الهيكل القانوني.

### 3.4 Reporting Structure

يجيب عن:

```text
كيف نريد عرض الأرقام؟
```

قد تريد الإدارة تقريرًا حسب:

- الدولة.
- القطاع.
- المنتج.
- قناة البيع.
- مدير المنطقة.
- نموذج العمل.

هذه أبعاد تحليلية، ولا يلزم أن تكون جميعها كيانات قانونية.

---

## 4. المستويات الرئيسية للهيكل التنظيمي

## 4.1 Group / Organization

أعلى مساحة عمل في النظام. قد تمثل مجموعة قابضة أو عميلًا في نظام SaaS.

مثال:

```text
Al Noor Holding Group
```

الحقول المقترحة:

```text
organizations
- id
- code
- legal_name
- display_name
- default_reporting_currency_id
- default_fiscal_calendar_id
- timezone
- status
```

### أثرها على النظام

تحدد:

- عزل بيانات العميل عن عميل آخر.
- إعدادات المجموعة.
- المستخدمين والصلاحيات العليا.
- دليل الحسابات المركزي.
- عملة التقارير الافتراضية.
- نطاق التوحيد.

في نظام متعدد المستأجرين، يجب أن يحمل كل كيان مالي `organization_id` أو يرتبط به بشكل يمكن التحقق منه.

---

## 4.2 Holding Company

الشركة القابضة قد تكون:

- مالكة لأسهم الشركات.
- جهة تمويل مركزية.
- جهة تقدم خدمات مشتركة.
- شركة لديها عمليات فعلية.
- أو كيانًا إداريًا محدود النشاط.

لا تفترض أن `Organization` و`Holding Company` متطابقان دائمًا.

قد يكون:

```text
Organization = المجموعة في التطبيق
Holding Company = كيان قانوني واحد داخل المجموعة
```

---

## 4.3 Legal Entity

هو أهم مستوى قانوني في النظام المالي.

```text
legal_entities
- id
- organization_id
- code
- legal_name
- country_id
- tax_registration_number
- functional_currency_id
- reporting_currency_id
- fiscal_calendar_id
- parent_entity_id
- ownership_percentage
- control_percentage
- consolidation_method
- is_active
```

### لماذا هو مهم؟

لأنه يحدد:

- صاحب المعاملة.
- الدفاتر المحلية.
- العملة الوظيفية.
- الضرائب.
- الفترة المحاسبية.
- التقارير القانونية.
- دخول الكيان في التوحيد.

### مثال

```text
Organization: Al Noor Group
Legal Entity: Al Noor Jordan Trading LLC
Country: Jordan
Functional Currency: JOD
```

الشركة الفرعية ليست مجرد فرع في جدول الفروع؛ فهي كيان قانوني له دورة مالية مستقلة.

---

## 4.4 Country / Jurisdiction

الدولة ليست بالضرورة كيانًا قانونيًا.

هي تحدد غالبًا:

- العملة المحلية.
- قوانين الضرائب.
- نوع التقارير القانونية.
- قواعد الفوترة.
- متطلبات الاحتفاظ بالسجلات.
- المنطقة الزمنية.

الجداول المقترحة:

```text
countries
- id
- iso_code
- name
- default_currency_id
- tax_jurisdiction_code
- timezone
```

قد يوجد أكثر من Legal Entity في الدولة نفسها، وقد يعمل كيان واحد في عدة دول عبر فروع أو تسجيلات ضريبية.

---

## 4.5 Business Unit

وحدة أعمال تستخدم لتقسيم النشاط التجاري، مثل:

```text
Retail
Professional Services
Manufacturing
Real Estate
SaaS
Corporate Services
```

يمكن أن تكون وحدة الأعمال:

- داخل كيان قانوني واحد.
- عابرة لعدة كيانات.
- مسؤولة عن منتج أو سوق.
- أداة إدارية وليست كيانًا قانونيًا.

### جدول مقترح

```text
business_units
- id
- organization_id
- code
- name
- parent_id
- owner_user_id
- is_active
```

لا تستخدم Business Unit بدل Legal Entity في القيود القانونية؛ هما مفهومان مختلفان.

---

## 4.6 Branch / Location

الفرع أو الموقع يصف أين يحدث النشاط.

مثال:

```text
Jordan Trading Co.
├── Amman Branch
├── Irbid Branch
└── Aqaba Branch
```

في النظام الحالي:

```text
Branch
  └── Department
        └── Expense
```

لكن في نظام المجموعة يجب ربط الفرع أولًا بالكيان القانوني:

```text
Legal Entity
  └── Branch
        └── Department
```

الحقول المقترحة:

```text
branches
- id
- legal_entity_id
- code
- name
- country_id
- city
- address
- timezone
- is_active
```

قد يكون للفرع مركز تكلفة أو أكثر، وقد تخدمه أقسام مشتركة.

---

## 4.7 Department

القسم وحدة إدارية أو وظيفية:

```text
Human Resources
Finance
Sales
Operations
IT
Marketing
```

الحقول المقترحة:

```text
departments
- id
- legal_entity_id
- branch_id
- code
- name
- parent_id
- manager_id
- is_active
```

لا تفترض أن كل قسم داخل فرع واحد. في الشركات الكبيرة قد يكون قسم المالية مركزيًا ويخدم عدة فروع.

عند الحاجة، استخدم علاقة مستقلة:

```text
department_entity_scope
 department_id
 legal_entity_id
```

أو:

```text
department_branch_scope
 department_id
 branch_id
```

---

## 4.8 Cost Center

مركز التكلفة هو وحدة نريد قياس تكلفتها وتعيين مسؤول عنها.

قد يساوي Department في شركة صغيرة، لكنه ليس بالضرورة مساويًا له.

مثال:

```text
Department: Operations
Cost Centers:
- Warehouse
- Delivery Fleet
- Customer Support
```

الحقول المقترحة:

```text
cost_centers
- id
- legal_entity_id
- code
- name
- parent_id
- department_id
- branch_id
- manager_id
- is_active
```

### الفرق بين Department وCost Center

| المفهوم | السؤال |
|---|---|
| Department | كيف نقسم الإدارة؟ |
| Cost Center | أين نحمّل التكلفة ومن المسؤول عنها؟ |

قد يكون قسم واحد عدة Cost Centers، وقد يجمع Cost Center تكاليف أكثر من قسم حسب سياسة الإدارة.

---

## 4.9 Profit Center

مركز الربح وحدة تقاس عليها الإيرادات والتكاليف والنتيجة.

مثال:

```text
Retail Stores
Online Sales
Corporate Services
```

قد يكون Profit Center:

- فرعًا.
- منتجًا.
- قناة بيع.
- منطقة.
- Business Unit.

لا يعني وجود Profit Center أنه كيان قانوني مستقل.

---

## 4.10 Project / Contract

المشروع أو العقد بُعد مؤقت أو طويل الأجل لتتبع الإيرادات والتكاليف.

```text
projects
- id
- legal_entity_id
- code
- name
- customer_id
- start_date
- end_date
- project_manager_id
- status
```

شركة الخدمات قد تحتاج المشروع لتسجيل:

- ساعات الموظفين.
- تكلفة الموردين.
- الإيراد.
- هامش الربح.

---

## 4.11 Team وUser Scope

المستخدم ليس جزءًا من الهيكل المالي بالضرورة، لكنه يحتاج Scope يحدد ما يستطيع رؤيته وتعديله.

مثال:

```text
User A: يرى شركة الأردن فقط
User B: يرى كل شركات السعودية
User C: يستطيع اعتماد ميزانيات المجموعة
```

جداول مقترحة:

```text
users
roles
permissions
user_organization_scopes
user_entity_scopes
user_branch_scopes
user_department_scopes
```

لا تعتمد على `role` وحده. الصلاحية تحتاج عادة إلى:

```text
Action Permission + Data Scope
```

---

## 5. الفرق بين Organization Structure وChart of Accounts

### Organization Structure يصف

```text
من يملك؟
أين يعمل؟
من يدير؟
أي كيان قانوني؟
أي دولة؟
أي فرع أو قسم؟
```

### Chart of Accounts يصف

```text
ما طبيعة المبلغ؟
هل هو أصل؟
هل هو التزام؟
هل هو إيراد؟
هل هو تكلفة؟
هل هو مصروف؟
```

### مثال

```text
Account: 610000 Salaries Expense
Entity: Saudi Services Co.
Branch: Riyadh
Department: Delivery
Cost Center: CC-DEL-001
```

`610000` ينتمي إلى COA.

أما `Saudi Services Co.` و`Riyadh` و`Delivery` و`CC-DEL-001` فتنتمي إلى Organization Structure أو الأبعاد المرتبطة به.

---

## 6. كيف يتداخلان في الحركة المالية؟

القيد أو الحركة المالية يحتاج عادة إلى الاثنين:

```text
Journal Entry Line
├── Account / Group Account
├── Legal Entity
├── Branch
├── Department
├── Cost Center
├── Project
├── Currency
├── Counterparty
└── Fiscal Period
```

### مثال مصروف

```text
Account: 620000 Marketing Expense
Legal Entity: Jordan Trading Co.
Branch: Amman
Department: Marketing
Cost Center: CC-MKT-001
Project: Winter Campaign
Currency: JOD
Amount: 12,000
```

الحساب يخبرنا **ماذا**، والهيكل يخبرنا **لمن وأين ومن المسؤول**.

### مثال إيراد

```text
Account: 410000 Product Revenue
Legal Entity: Saudi Services Co.
Business Unit: Enterprise Services
Profit Center: Riyadh Sales
Customer: Customer 55
Currency: SAR
Amount: 300,000
```

---

## 7. هل نضع Entity داخل كود الحساب؟

لا يفضل ذلك.

### تصميم غير مرن

```text
JO-410000
SA-410000
UK-410000
```

المشاكل:

- تكرار الحساب نفسه لكل شركة.
- صعوبة تغيير الدولة أو الملكية.
- صعوبة التوحيد.
- تضخم COA.
- خلط طبيعة الحساب بمالك الحركة.

### تصميم أفضل

```text
Group Account: 410000 Product Revenue
Entity: Jordan Trading Co.
```

وإذا احتاجت الشركة حسابًا محليًا:

```text
Local Account: JO-4101 Product Sales
Maps to Group Account: 410000 Product Revenue
```

---

## 8. متى يكون Organization Structure داخل شجرة؟

أحيانًا نحتاج شجرة تنظيمية للعرض أو الصلاحيات:

```text
Group
└── Region
    └── Legal Entity
        └── Branch
            └── Department
                └── Cost Center
```

هذه الشجرة مفيدة إذا كانت العلاقات ثابتة وواضحة.

لكن لا تحاول إجبار كل العلاقات على شجرة واحدة؛ قد توجد علاقات متقاطعة:

```text
Legal Entity A
  ├── Branch Amman
  └── Shared Finance Department

Shared Finance Department
  ├── يخدم Legal Entity A
  ├── يخدم Legal Entity B
  └── يخدم Legal Entity C
```

في هذه الحالة نحتاج جداول ربط Many-to-many بدل `parent_id` فقط.

---

## 9. نوعان من العلاقات داخل الهيكل

### Hierarchical Relationship

علاقة أب وابن:

```text
Group → Entity → Branch → Department
```

تستخدم للتجميع والصلاحيات الموروثة.

### Scope / Assignment Relationship

علاقة ارتباط أو نطاق:

```text
Department Finance يخدم عدة Entities
Cost Center يوزع على عدة Branches
Manager مسؤول عن عدة Departments
```

الجداول المحتملة:

```text
entity_business_units
department_entities
department_branches
cost_center_projects
manager_scopes
```

لا تستخدم `parent_id` لمعالجة كل الحالات.

---

## 10. الملكية ليست هي التبعية الإدارية

قد تملك الشركة القابضة 60% من شركة، لكن الإدارة التشغيلية تكون مشتركة أو مستقلة.

لذلك افصل:

```text
ownership_percentage
control_percentage
management_scope
consolidation_method
```

مثال:

```text
Ownership: 40%
Control: نعم بسبب اتفاقية تصويت
Consolidation: Full consolidation
```

أو:

```text
Ownership: 30%
Control: لا
Consolidation: Associate / Equity method حسب السياسة
```

هذه قرارات مالية وقانونية تحتاج قواعد المجموعة، ولا يجب استنتاجها من نسبة الملكية وحدها.

---

## 11. نموذج بيانات الهيكل التنظيمي

### organizations

```text
id
code
name
group_type
default_reporting_currency_id
status
created_at
updated_at
```

### legal_entities

```text
id
organization_id
code
legal_name
short_name
country_id
tax_number
functional_currency_id
fiscal_calendar_id
parent_entity_id
ownership_percentage
control_percentage
consolidation_method
valid_from
valid_to
status
```

### branches

```text
id
legal_entity_id
code
name
country_id
city
address
is_active
```

### departments

```text
id
code
name
parent_id
manager_id
is_active
```

### department_entity_assignments

```text
id
department_id
legal_entity_id
valid_from
valid_to
```

### department_branch_assignments

```text
id
department_id
branch_id
valid_from
valid_to
```

### cost_centers

```text
id
code
name
legal_entity_id
branch_id
department_id
parent_id
manager_id
is_active
```

### business_units

```text
id
organization_id
code
name
parent_id
owner_id
is_active
```

### entity_business_unit_assignments

```text
id
legal_entity_id
business_unit_id
valid_from
valid_to
```

---

## 12. Organization Structure وBudgeting

الميزانية لا تعتمد على الحساب وحده.

سطر الميزانية المتقدم قد يمثل:

```text
Budget Version
+ Legal Entity
+ Fiscal Period
+ Group Account
+ Cost Center
+ Department
+ Branch
+ Business Unit
+ Project
+ Currency
```

### مثال

```text
Budget Version: 2027 Approved
Entity: Jordan Trading Co.
Branch: Amman
Department: Sales
Cost Center: CC-SALES-AMM
Account: 620000 Marketing Expense
Period: 2027-03
Amount: 15,000 JOD
```

### قاعدة تصميم

لا تكرر الميزانية نفسها لكل مستوى إلا إذا كان لكل مستوى مبلغ مستقل.

مثال:

- Budget على مستوى Group Account وEntity فقط: لا تضف Branch وهميًا.
- Budget على مستوى Branch: يجب أن يكون Branch حقيقيًا تابعًا للـ Entity.
- Budget مركزي يخدم عدة كيانات: استخدم Allocation Rule بدل نسخ عشوائية.

---

## 13. Organization Structure وActuals

الحركة الفعلية يجب أن تشير إلى المالك والمسؤول:

```text
actual_transaction
- legal_entity_id
- account_id
- branch_id
- department_id
- cost_center_id
- business_unit_id
- project_id
- transaction_date
- amount
- currency_id
```

### قواعد اتساق

```text
branch.legal_entity_id = transaction.legal_entity_id
cost_center.legal_entity_id = transaction.legal_entity_id
department assignment صالح في تاريخ الحركة
account صالح في تاريخ الحركة
currency متوافقة مع سياسة الكيان
```

لا يكفي أن تكون IDs موجودة؛ يجب أن تكون العلاقات منطقية زمنيًا.

---

## 14. أثر الهيكل على الصلاحيات

### صلاحية على المجموعة

تستخدم للإدارة العليا أو فريق المجموعة.

### صلاحية على Legal Entity

تستخدم لفريق المالية المحلي.

### صلاحية على Branch

تستخدم مدير الفرع.

### صلاحية على Department أو Cost Center

تستخدم مدير القسم أو مالك الميزانية.

### صلاحية Account

تحدد أي حساب يمكن إنشاؤه أو تعديله أو اعتماده.

القرار النهائي يجب أن يجمع بين:

```text
Role: ماذا يستطيع المستخدم أن يفعل؟
Scope: على أي كيانات أو فروع أو حسابات؟
Workflow: في أي حالة يسمح بالفعل؟
```

### مثال

```text
Budget Editor
- يستطيع تعديل budget_lines
- داخل Entity Jordan فقط
- للفترة المفتوحة فقط
- لا يستطيع اعتماد الميزانية
```

```text
Group Controller
- يرى كل Entities
- يستطيع اعتماد Mapping
- يستطيع تشغيل Consolidation
- لا يعدل القيود المحلية مباشرة
```

---

## 15. أثر الهيكل على سير الموافقات

قد تختلف الموافقات حسب:

- الكيان.
- المبلغ.
- الحساب.
- الفرع.
- مركز التكلفة.
- نوع الميزانية.
- العملة.

مثال:

```text
Budget Line أقل من 10,000:
مدير Cost Center

من 10,000 إلى 100,000:
مدير Entity + Finance Manager

أكثر من 100,000:
Group Finance + Executive Approval
```

الجداول المقترحة:

```text
workflow_definitions
workflow_scopes
approval_thresholds
approval_requests
approval_actions
```

لا تجعل قواعد الموافقة hard-coded على اسم القسم فقط؛ اجعلها قابلة للإصدار والتاريخ.

---

## 16. Organization Structure وConsolidation

التوحيد يحتاج معرفة:

```text
أي كيانات تدخل؟
ما نسبة الملكية؟
هل توجد سيطرة؟
ما طريقة التوحيد؟
ما العملة الوظيفية؟
ما الطرف المقابل لكل معاملة؟
```

### جداول التوحيد

```text
consolidation_groups
consolidation_scopes
consolidation_periods
ownership_periods
intercompany_relationships
elimination_rules
```

### مثال

```text
Consolidation Group: Al Noor Group
Period: 2026-12
Included Entities:
- Holding Co.
- Jordan Trading Co.
- Saudi Services Co.
Excluded:
- Associate Egypt Manufacturing Co.
```

المجموعة في التقرير ليست مجرد مجموع `organization_id`; لها Scope محدد لكل فترة.

---

## 17. Organization Structure وIntercompany

عند وجود أكثر من Legal Entity، يجب تمييز الشركة المقابلة:

```text
Entity: Holding Co.
Counterparty Entity: Saudi Services Co.
Account: Intercompany Loan Receivable
```

الحقل الأساسي:

```text
counterparty_entity_id
```

ولا يكفي استخدام `customer_id` أو `supplier_id`، لأن الطرف المقابل هنا كيان داخلي في المجموعة.

### متطلبات التحقق

```text
counterparty_entity_id != legal_entity_id
العلاقة بين الكيانين صالحة في تاريخ المعاملة
الحساب يسمح بتعامل intercompany
العملة وسعر الصرف موجودان
```

---

## 18. Organization Structure وChart of Accounts: نموذج المقارنة

| السؤال | Organization Structure | Chart of Accounts |
|---|---|---|
| ماذا يصف؟ | المؤسسة وملكية وتشغيل المسؤوليات | طبيعة الرقم المالي |
| أمثلة | Entity، Branch، Department | Cash، Revenue، Salaries |
| هل هو قانوني؟ | قد يكون Legal Entity قانونيًا | الحساب جزء من الدفاتر والسياسة |
| هل يتغير مع المكان؟ | نعم حسب الشركات والدول | ليس بالضرورة |
| هل يجمع التقارير؟ | حسب الكيان والدولة والفرع | حسب نوع الإيراد والمصروف |
| علاقته بالحركة | يحدد المالك والمكان والمسؤول | يحدد الحساب المدين أو الدائن |
| هل يدخل في التوحيد؟ | يحدد نطاق الكيانات | يحدد تصنيف Group COA |
| هل يستخدم للصلاحيات؟ | نعم بشكل أساسي | نعم حسب أدوار الحساب |

---

## 19. ثلاث خرائط يجب عدم خلطها

### 19.1 Ownership Mapping

```text
Holding → Subsidiary
```

يصف الملكية والسيطرة.

### 19.2 Organization Assignment

```text
Entity → Branch → Department → Cost Center
```

يصف الهيكل التشغيلي.

### 19.3 Account Mapping

```text
Local Account → Group Account
```

يصف تصنيف الأرقام المالية.

قد تتواجد الخرائط الثلاث في نفس التقرير، لكنها ليست علاقة واحدة.

---

## 20. العلاقة مع Group COA وLocal COA

```text
Organization
├── Legal Entity A
│   ├── Local COA A
│   └── Organization Units A
├── Legal Entity B
│   ├── Local COA B
│   └── Organization Units B
└── Group COA
```

`Group COA` يتبع المجموعة.

`Local COA` يتبع الكيان القانوني.

`Branch` و`Department` يتبعان الهيكل التشغيلي للكيان، وليس دليل الحسابات.

### مثال

```text
Group Account: 610000 Salaries Expense

Local Account A: 5110 Salaries - Jordan
Local Account B: 7201 Staff Costs - UK
Local Account C: 6110 Payroll - Saudi
```

الثلاثة يمكن أن ترتبط بنفس Group Account، مع اختلاف الكيانات والأبعاد.

---

## 21. هل لكل شركة COA مختلف؟

نعم، قد يكون لكل شركة Local COA مختلف، لكن نحتاج سياسة موحدة للمجموعة.

### Group COA يحدد

```text
التقارير العليا
تعريف الإيرادات والتكاليف
التوحيد
المقارنة بين الشركات
```

### Local COA يحدد

```text
التشغيل المحلي
التقارير القانونية
الضرائب المحلية
تفاصيل نشاط الشركة
```

### Mapping

```text
local_account_id
→ group_account_id
```

ويجب أن يدعم تاريخ السريان والإصدار والمراجعة.

---

## 22. نموذج متعدد الأبعاد للحركة

السطر المالي الكامل قد يكون:

```text
organization_id
legal_entity_id
country_id
branch_id
department_id
cost_center_id
profit_center_id
business_unit_id
project_id
customer_id
supplier_id
counterparty_entity_id
local_account_id
group_account_id
currency_id
fiscal_period_id
scenario_id
amount
```

ليس معنى هذا أن كل الحقول يجب أن تكون غير فارغة دائمًا.

الحساب أو نوع الحركة يحدد الحقول الإلزامية:

```text
Salaries Expense → Cost Center required
Intercompany Loan → Counterparty required
Project Revenue → Project required
VAT Account → Tax Code required
Cash Account → Bank Account required
```

---

## 23. الأبعاد المشتركة والكيانات المنفصلة

### كيان مستقل

استخدم جدولًا مستقلًا عندما تكون للبيانات:

- دورة حياة.
- خصائص كثيرة.
- علاقات.
- صلاحيات.
- تاريخ تغييرات.

أمثلة:

```text
legal_entities
branches
cost_centers
business_units
```

### Dimension بسيط

يمكن استخدام Dimension عندما نحتاج تصنيفًا موحدًا للقراءة والتحليل.

أمثلة:

```text
dim_country
dim_currency
dim_business_model
```

في الطبقة التشغيلية قد يكون Business Model كيانًا، وفي الطبقة التحليلية يظهر كـ Dimension.

---

## 24. التاريخ الفعال Effective Dating

الهيكل التنظيمي يتغير بمرور الوقت:

- فرع ينتقل إلى شركة أخرى.
- قسم يتغير مديره.
- شركة تدخل المجموعة أو تخرج منها.
- Cost Center يغلق.
- Business Unit يعاد تنظيمه.

لا تستخدم `is_active` فقط إذا كانت التقارير التاريخية مهمة.

استخدم:

```text
valid_from
valid_to
```

أو جداول تاريخية:

```text
entity_ownership_history
branch_assignment_history
department_manager_history
cost_center_history
```

### قاعدة تاريخية

يجب أن يستخدم التقرير العلاقة التي كانت صالحة في تاريخ الحركة، وليس العلاقة الحالية فقط.

---

## 25. مثال إعادة تنظيم

في يناير:

```text
Department: Sales
Branch: Amman
Cost Center: CC-SALES-AMM
```

في يوليو تم فصل المبيعات إلى:

```text
Sales Retail
Sales Enterprise
```

لا نعيد تفسير مصروفات يناير على أنها Enterprise أو Retail إذا لم تكن هذه المعلومة موجودة.

التصميم الصحيح:

```text
Old assignment valid_to = 2026-06-30
New assignments valid_from = 2026-07-01
```

أما التقارير الإدارية المعاد تصنيفها فتحتاج قاعدة Restatement واضحة منفصلة عن البيانات الأصلية.

---

## 26. قواعد اتساق البيانات

### Entity وBranch

```text
branch.legal_entity_id = transaction.legal_entity_id
```

### Department وEntity

```text
department assignment valid for entity and transaction date
```

### Cost Center وBranch

```text
cost_center.branch_id matches transaction branch when required
```

### Group Account وLocal Account

```text
mapping valid for entity and transaction date
```

### Currency

```text
transaction currency is allowed for entity
exchange rate exists when conversion is needed
```

### Period

```text
period belongs to entity fiscal calendar
period is open for posting
```

هذه القيود يجب تطبيقها في Django وPostgreSQL وطبقة التحليل حسب طبيعة القاعدة.

---

## 27. أثر التصميم على قاعدة البيانات

### تصميم غير مناسب

```text
finance_records
- company_name
- branch_name
- department_name
- account_name
- amount
```

مشاكله:

- تكرار الأسماء.
- صعوبة تغيير الاسم.
- عدم وجود IDs ثابتة.
- ضعف العلاقات.
- أخطاء spelling.
- صعوبة التوحيد.

### تصميم أفضل

```text
legal_entities
branches
departments
group_accounts
entity_accounts
account_mappings
journal_entries
journal_entry_lines
```

وتحمل الحركة IDs:

```text
legal_entity_id
branch_id
department_id
group_account_id
```

---

## 28. تصميم Django التشغيلي

يمكن تقسيم التطبيق إلى مجالات:

```text
organization/
- Organization
- LegalEntity
- Country
- Currency
- OwnershipPeriod

structure/
- Branch
- Department
- CostCenter
- BusinessUnit
- Project

accounting/
- GroupAccount
- EntityAccount
- AccountMapping
- JournalEntry
- JournalEntryLine

budgeting/
- BudgetPlan
- BudgetVersion
- BudgetLine

consolidation/
- IntercompanyTransaction
- EliminationEntry
- ConsolidationRun
```

لا يلزم أن تكون Django apps منفصلة في أول نسخة، لكن فصل المفاهيم في النماذج والخدمات مهم.

---

## 29. تصميم dbt التحليلي

يبني dbt أبعادًا موحدة:

```text
dim_organization
dim_legal_entity
dim_country
dim_branch
dim_department
dim_cost_center
dim_business_unit
dim_project
dim_group_account
dim_local_account
dim_currency
dim_date
```

ثم facts:

```text
fact_journal_lines
fact_expenses
fact_budget
fact_intercompany
fact_eliminations
```

ثم marts:

```text
entity_trial_balance
entity_profit_and_loss
group_profit_and_loss
budget_vs_actual_by_entity
budget_vs_actual_by_cost_center
intercompany_reconciliation
consolidated_financials
```

### Grain مهم

```text
fact_journal_lines:
صف واحد لكل سطر قيد

fact_budget:
صف واحد لكل نسخة + فترة + حساب + كيان + أبعاد الميزانية

entity_trial_balance:
صف واحد لكل فترة + كيان + حساب + أبعاد التجميع

group_profit_and_loss:
صف واحد لكل فترة + Group Account + Reporting Scope
```

---

## 30. أثر التصميم على Cube وDashboard

يجب أن تعرض طبقة Semantic Layer مقاييس وأبعاد واضحة.

### Measures

```text
Actual Amount
Budget Amount
Variance Amount
Variance Percentage
Revenue
Operating Expenses
EBITDA
```

### Dimensions

```text
Group Account
Legal Entity
Country
Branch
Department
Cost Center
Business Unit
Project
Fiscal Period
Scenario
```

### مثال سؤال Dashboard

```text
أظهر مصاريف الرواتب الفعلية
لشركة السعودية
في فرع الرياض
لقسم Delivery
خلال الربع الأول
مقارنة بالميزانية المعتمدة
```

هذا السؤال يحتاج:

```text
Account + Entity + Branch + Department + Period + Scenario
```

وليس حسابًا واحدًا اسمه `SA-RIY-DEL-SALARIES`.

---

## 31. أثر الهيكل على الاستيراد Ingestion

عند استيراد ملف من شركة فرعية، يجب معرفة:

```text
source_system
source_entity
source_account_code
source_branch_code
source_department_code
transaction_date
currency
amount
```

ثم يمر عبر Mapping:

```text
source_entity_code → legal_entity_id
source_account_code → entity_account_id
entity_account_id → group_account_id
source_branch_code → branch_id
```

### لا تعتمد على الاسم فقط

الأفضل أن يحتوي المصدر على Codes ثابتة. إذا لم توجد، استخدم جدول Mapping ومراجعة بشرية:

```text
source_value
normalized_value
target_id
mapping_status
reviewed_by
```

---

## 32. أثر الهيكل على Budget Ownership

لكل سطر ميزانية يجب تحديد مالك أو مسؤول:

```text
budget_owner_id
cost_center_id
legal_entity_id
approval_scope
```

### مثال

```text
Cost Center Owner: مدير التسويق
Entity Finance Reviewer: المدير المالي للشركة
Group Reviewer: Group FP&A
```

لا تجعل كل المستخدمين يرون أو يعدلون كل الميزانيات.

---

## 33. الفرق بين Cost Center وProfit Center وBusiness Unit

| المفهوم | الغرض الأساسي | يحتاج إيرادًا؟ |
|---|---|---:|
| Department | تنظيم إداري | ليس بالضرورة |
| Cost Center | قياس وتحميل التكلفة | لا |
| Profit Center | قياس الربح | نعم غالبًا |
| Business Unit | تقسيم النشاط التجاري | حسب التصميم |
| Legal Entity | كيان قانوني وتقارير وضرائب | حسب نشاطه |
| Branch | موقع أو وحدة تشغيل | حسب نشاطه |

قد تمثل وحدة واحدة أكثر من مفهوم، لكن لا تفترض التطابق.

---

## 34. مصفوفة القرار: أين أضع الحقل؟

| السؤال | المكان الأفضل |
|---|---|
| ما طبيعة المبلغ؟ | Account |
| من يملك المعاملة قانونيًا؟ | Legal Entity |
| في أي دولة؟ | Country / Jurisdiction |
| أين حدثت؟ | Branch / Location |
| أي قسم مسؤول؟ | Department |
| أين نحمّل التكلفة؟ | Cost Center |
| من يحقق الربح؟ | Profit Center |
| لأي نشاط تجاري؟ | Business Unit |
| لأي منتج أو عقد؟ | Product / Project |
| مع أي شركة داخلية؟ | Counterparty Entity |
| بأي عملة؟ | Currency |
| لأي فترة؟ | Fiscal Period |
| لأي نسخة خطة؟ | Budget Version |
| كيف يصنف محليًا للمجموعة؟ | Account Mapping |

---

## 35. أخطاء تصميم شائعة

### اعتبار Group وLegal Entity الشيء نفسه

يؤدي إلى مشاكل في التوحيد والصلاحيات.

### وضع Branch في COA

يؤدي إلى تضخم الحسابات. الفرع Dimension مستقل.

### اعتبار Department دائمًا Cost Center

قد يكون صحيحًا في شركة صغيرة فقط. في الشركات الكبيرة افصل الاثنين.

### استخدام شجرة واحدة لكل العلاقات

الملكية والإدارة والتشغيل والتقارير ليست دائمًا شجرة واحدة.

### تجاهل تاريخ التغيير

يعطي تقارير تاريخية خاطئة بعد إعادة التنظيم.

### وضع Business Model في account code

يمنع إضافة نموذج جديد بسهولة.

### عدم حفظ Counterparty

يجعل Intercompany reconciliation شبه مستحيل.

### ربط المستخدم بالاسم لا بالـ ID

الأسماء تتغير، والصلاحيات يجب أن تعتمد على معرفات ونطاقات ثابتة.

### جعل dbt مسؤولًا عن الصلاحيات التشغيلية

dbt يبني التحليل، لكنه ليس نظام authorization للمعاملات المحلية.

---

## 36. نموذج دورة حركة مالية كاملة

```text
1. المصدر يرسل الحركة
2. نحدد المصدر والكيان القانوني
3. نتحقق من الفترة المفتوحة
4. نحدد Local Account
5. نطبق Account Mapping
6. نتحقق من الأبعاد المطلوبة
7. نتحقق من العملة وسعر الصرف
8. نسجل الحركة التشغيلية
9. نثبت القيد أو نرسله للموافقة
10. يحمله dbt إلى fact
11. يظهر في Cube حسب الحساب والهيكل
12. يدخل التوحيد إذا كان الكيان ضمن النطاق
```

---

## 37. الحد الأدنى المقترح للمنتج

### المرحلة الأولى

```text
organizations
legal_entities
countries
currencies
branches
departments
cost_centers
group_accounts
entity_accounts
account_mappings
fiscal_periods
```

### المرحلة الثانية

```text
users
roles
permissions
user_entity_scopes
budget_plans
budget_versions
budget_lines
approval_requests
audit_logs
```

### المرحلة الثالثة

```text
journal_entries
journal_entry_lines
business_units
projects
customers
suppliers
intercompany_transactions
```

### المرحلة الرابعة

```text
consolidation_scopes
elimination_entries
ownership_periods
exchange_rates
consolidated_marts
```

---

## 38. قواعد لا تؤجلها

حتى في MVP يجب تثبيت:

1. `organization_id` لعزل بيانات المجموعة.
2. `legal_entity_id` لكل رقم مالي.
3. العملة الوظيفية لكل كيان.
4. العلاقة بين الفرع والكيان.
5. Group COA وLocal COA بكيانين واضحين.
6. Account Mapping بتاريخ سريان.
7. تعريف Grain لكل جدول تحليلي.
8. صلاحيات على مستوى الكيان أو النطاق.
9. حفظ المصدر والتاريخ للحركات المستوردة.
10. عدم خلط قيود التوحيد بالقيود المحلية.

---

## 39. مثال مجموعة كاملة

```text
Organization: Al Noor Holding Group

Holding Entity: Al Noor Holdings Ltd
Country: UAE
Functional Currency: AED

Entity 1: Al Noor Jordan Trading
Country: Jordan
Currency: JOD
Branches: Amman, Irbid
Business Unit: Trading

Entity 2: Al Noor Saudi Services
Country: Saudi Arabia
Currency: SAR
Branches: Riyadh, Jeddah
Business Unit: Professional Services

Entity 3: Al Noor UK Technology
Country: United Kingdom
Currency: GBP
Office: London
Business Unit: SaaS
```

### مصروف واحد داخل المجموعة

```text
Group Account: 610000 Salaries Expense

Entity: Al Noor Saudi Services
Branch: Riyadh
Department: Delivery
Cost Center: CC-DEL-RUH
Business Unit: Professional Services
Currency: SAR
Amount: 250,000
```

### كيف يظهر؟

- في دفتر الشركة: بحساب محلي سعودي.
- في تقرير المجموعة: Group Account `610000`.
- في تقرير الدولة: Saudi Arabia.
- في تقرير الفرع: Riyadh.
- في تقرير النشاط: Professional Services.
- في التوحيد: يدخل إذا كانت الشركة ضمن Consolidation Scope.

---

## 40. أسئلة يجب حسمها مع أصحاب العمل

1. هل النظام يمثل مجموعة واحدة أم عدة عملاء مستقلين؟
2. هل كل شركة تملك دفترًا قانونيًا مستقلًا؟
3. هل الفروع كيانات قانونية أم مواقع فقط؟
4. هل الأقسام مركزية وتخدم عدة شركات؟
5. هل نحتاج Cost Centers مختلفة عن Departments؟
6. هل التقارير حسب Business Unit أم Legal Entity أم الاثنين؟
7. ما العملة الوظيفية وعملة التقارير لكل كيان؟
8. هل توجد سنوات مالية مختلفة؟
9. هل Group COA موحد أم لكل قطاع مجموعة فرعية؟
10. من يملك ويعتمد تغييرات COA؟
11. من يراجع Account Mapping؟
12. هل نحتاج تقارير قانونية محلية؟
13. هل نحتاج توحيدًا كاملًا أم تقارير إدارية فقط؟
14. كيف نعالج التعاملات بين الشركات؟
15. ما الذي يجب أن يبقى تاريخيًا عند إعادة الهيكلة؟

---

## الخلاصة

التصميم الصحيح يفرق بين ثلاث طبقات:

```text
Ownership / Legal Structure
من يملك ومن يدخل في التوحيد؟

Operating Organization Structure
من يدير وأين يحدث النشاط ومن يتحمل المسؤولية؟

Chart of Accounts
ما طبيعة الرقم المالي وكيف يصنف محاسبيًا؟
```

والحركة المالية تربط الطبقات دون دمجها:

```text
Journal Line
= Account
+ Legal Entity
+ Organization Dimensions
+ Currency
+ Period
+ Source
```

القاعدة الذهبية:

```text
Chart of Accounts يجيب: ماذا حدث ماليًا؟
Organization Structure يجيب: لمن وأين ومن المسؤول؟
Consolidation Structure يجيب: من يدخل في تقرير المجموعة وكيف؟
```
