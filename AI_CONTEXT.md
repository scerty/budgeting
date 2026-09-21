# AI Context: Finance Budgeting Stack

هذه الوثيقة هي نقطة الدخول لأي Agent يعمل على هذا المستودع. اقرأها قبل تعديل
البيانات أو الـ dbt models أو الـ dashboard. الهدف هو الحفاظ على مسار البيانات
والـ grain وعدم إعادة إدخال بيانات demo في actuals الحقيقية.

المخطط المرئي لعلاقات الجداول موجود في
[docs/DATA_MODEL_DIAGRAM_AR.md](docs/DATA_MODEL_DIAGRAM_AR.md).

## 1. تعريف المشروع

هذا مستودع تطوير محلي لمنصة تحليل مالي مبنية على:

- Django 5.2 لتشغيل النماذج التشغيلية وعمليات ingestion.
- PostgreSQL 16 كمخزن التطبيق والطبقة التحليلية.
- dbt PostgreSQL لبناء staging وintermediate وanalytics Gold.
- Cube.js كطبقة semantic layer.
- Angular dashboard لعرض المؤشرات والمقارنات.
- ERPNext v16 كمصدر خارجي تجريبي للقيود الفعلية عبر REST API.

المسار التشغيلي الحالي:

```text
ERPNext REST API
    -> Django ingest_erpnext
    -> public.finance_rawjournalline
    -> dbt stg_journal_lines
    -> analytics.fact_journal_lines
    -> int_actuals_budget_ready
    -> analytics.budget_vs_actual / budget_vs_actual_month
    -> Cube.js
    -> Angular dashboard
```

Airbyte وClickHouse خارج المسار التشغيلي الحالي. لا تعيد إضافتهما أو تجعل
dashboard يعتمد عليهما إلا بطلب صريح.

## 2. نقاط التشغيل

شغّل الأوامر من جذر المستودع:

```bash
cd /opt/finance-stack-postgres
```

الخدمات الأساسية:

| الخدمة | العنوان أو الاستخدام |
|---|---|
| Dashboard | `http://localhost:14200/` |
| Cube API | `http://localhost:14000/` |
| Django | `http://localhost:18001/` |
| PostgreSQL من المضيف | `192.168.100.20:15432` |
| ERPNext demo | `http://localhost:18080` |

تشغيل Finance Stack:

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100 dashboard
```

إعادة بناء dbt بالكامل بعد تغيير المصادر أو المارت:

```bash
docker compose run --rm --no-deps dbt \
  dbt build --profiles-dir /root/.dbt --full-refresh
```

إعادة بناء dashboard بعد تغيير Angular أو Cube schema:

```bash
docker compose up -d --build dashboard
```

نجاح dbt المتوقع في الحالة الحالية هو `PASS=421 WARN=0 ERROR=0`، لكن يجب
تشغيل الأمر فعليًا بعد أي تغيير وعدم افتراض أن الرقم سيبقى ثابتًا.

## 3. ERPNext التجريبي

ERPNext يعمل في Compose مستقل وقاعدة MariaDB مستقلة. لا يتصل Django بقاعدة
MariaDB مباشرة؛ الاتصال يتم عبر REST:

```bash
docker compose -f compose.erpnext.yml up -d
docker compose -f compose.erpnext.yml ps
```

بيانات الدخول المحلية الحالية:

```text
Administrator / admin
```

اختبار REST:

```bash
curl -fsS -c /tmp/erpnext.cookies \
  -H 'Content-Type: application/json' \
  -d '{"usr":"Administrator","pwd":"admin"}' \
  http://localhost:18080/api/method/login

curl -fsS -b /tmp/erpnext.cookies \
  'http://localhost:18080/api/resource/GL%20Entry?limit_page_length=5'
```

استيراد GL Entry إلى Django:

```bash
docker compose exec django python manage.py ingest_erpnext \
  --organization DEMO \
  --username Administrator \
  --password admin
```

الأمر idempotent ويستخدم المصدر والمفتاح وhash لمنع النسخ المكررة. في العمل
الفعلـي مرر كلمة المرور عبر `ERPNEXT_PASSWORD` بدل وضعها في shell.

مزامنة master data:

```bash
docker compose exec django python manage.py sync_erpnext_master_data \
  --organization DEMO \
  --branch-company "Finance Demo (Demo)" \
  --username Administrator \
  --password admin
```

الأمر يزامن Company وAccount وCost Center وBranch. ويمكن بناء هيكل Django
المحلي idempotently عبر:

```bash
docker compose exec django python manage.py build_demo_group_structure
```

الأوامر الأخرى المهمة:

```text
seed_demo                 بيانات مصاريف Django التعليمية فقط
seed_planning_demo        budget/planning demo القابل للتكرار
ingest_erpnext            استيراد GL Entry إلى RawJournalLine
sync_erpnext_master_data  مزامنة أبعاد ERPNext
build_demo_group_structure بناء holding/entities/branches/departments
```

## 4. ملكية البيانات وقاعدة عدم التكرار

### Actuals

المصدر التشغيلي للـ actuals هو ERPNext عندما توجد ERPNext journals للمنظمة:

```text
RawJournalLine
    -> fact_journal_lines
    -> int_actuals_budget_ready.erpnext_actuals
```

`int_actuals_budget_ready.sql` يقرأ ERPNext فقط مع:

```sql
where j.source_system = 'erpnext'
```

بيانات `finance_expense` ذات `source_system = 'django'` ليست actuals بديلة
بشكل دائم. تستخدم فقط كـ fallback عندما لا توجد ERPNext journals للمنظمة:

```text
demo_actuals only when NOT EXISTS ERPNext journals for the organization
```

لا تجمع المسارين يدويًا ولا تضف `seed_demo` إلى actuals إذا كانت ERPNext
journals موجودة؛ هذا يسبب double counting.

### Budget

الـ budget الحالي تجريبي:

```text
amount: 7,000 USD
organization/entity: DEMO-JO
group account: 600000
branch: AMM
```

أما actual ERPNext الحالي فيمثل:

```text
organization/entity: ERP-FDD
group account: COST-OF-GOODS-SOLD-FDD
cost center: Main - FDD
```

هذان البعدان مختلفان، لذلك ظهور budget وactual في صفين منفصلين صحيح تقنيًا.
لا تنشئ merge صامتًا بينهما. للحصول على مقارنة مالية حقيقية يجب تحميل budget
مرتبط بـ ERP-FDD والحساب ERPNext نفسه، أو إنشاء mapping صريح ومُوثق.

## 5. dbt والـ grain

المخطط الفيزيائي:

```text
public              Django operational tables and raw ingestion
analytics           dbt dimensions, facts, marts
```

أهم النماذج:

| النموذج | المسؤولية |
|---|---|
| `fact_journal_lines` | صف فعّال لكل سطر قيد ERPNext مع debit/credit/signed amount |
| `fact_budget` | صف لكل budget line وأبعاده التشغيلية |
| `int_actuals_budget_ready` | توحيد budget وERPNext actuals وdemo fallback |
| `budget_vs_actual` | مقارنة سنوية حسب الأبعاد |
| `budget_vs_actual_month` | مقارنة شهرية حسب الشهر وكل الأبعاد |
| `dim_legal_entity` | وصف الكيان القانوني |
| `dim_group_account` | المجموعة الحسابية |
| `dim_entity_account` | الحساب التفصيلي المرتبط بالكيان |
| `dim_branch` | الفرع |
| `dim_department` | القسم |
| `dim_cost_center` | مركز التكلفة |

الـ grain في `budget_vs_actual_month` هو:

```text
organization
fiscal_period
legal_entity
group_account
entity_account
branch
department
cost_center
profit_center
business_unit
project
currency
month_start
```

اختبار uniqueness موجود في:

```text
dbt/project/tests/budget_vs_actual_month_grain.sql
```

إذا أضفت dimension جديدة إلى المارت، أضفها إلى:

1. budget branch.
2. actuals branch.
3. `group by` في CTE `aggregated`.
4. final dimension join أو column.
5. Cube schema.
6. query وrow interface في Angular.
7. grain test إذا تغير المفتاح.

لا تضف dimension في Cube فقط إذا لم تكن موجودة في `analytics`.

## 6. Budget الشهري

لا يوجد شهر على `BudgetLine` الحالي. لذلك يقوم
`budget_vs_actual_month.sql` بتوسيع budget line على أشهر الفترة المالية عبر
`generate_series` وتوزيع المبلغ بالتساوي.

السلوك الحالي:

- كل شهر يأخذ `amount / month_count`.
- الشهر الأخير يأخذ remainder الحسابي حتى يساوي مجموع الأشهر المبلغ السنوي
  تمامًا.
- عبارة الواجهة `Equal monthly allocation` تصف هذا السلوك.

هذا توزيع تقني مؤقت، وليس forecast شهريًا حقيقيًا. عند توفر monthly budget أو
driver يجب تعديل المارت ليستخدم الشهر أو driver بدل التوزيع المتساوي.

## 7. Dashboard وCube

Cube يقرأ من `analytics` فقط. عقد المقارنة الشهرية هو:

```text
cube/schema/BudgetVsActualMonth.js
```

المقاييس:

```text
budgetAmount
actualAmount
varianceAmount = actual - budget
```

الأبعاد المعروضة تشمل:

```text
organization
fiscal period/year
month
legal entity
group account
branch
department
currency
```

في dashboard:

- الفلاتر العامة: Organization وFiscal period وScenario version وBranch.
- جدول `Budget vs actual by group` يعرض تجميعًا حسب group account مع الأبعاد،
  ثم التفاصيل الشهرية تحته.
- توجد فلاتر محلية للحساب، الكيان القانوني، القسم، والعملة.
- جدول branch الشهري مستقل.

الملفات الأساسية:

```text
dashboard/src/app/app.ts
dashboard/src/app/app.html
dashboard/src/app/app.css
cube/schema/BudgetVsActualMonth.js
```

لا تجعل Angular ينفذ business aggregation أو إزالة التكرار؛ هذه مسؤولية dbt
وCube. Angular يطلب dimensions/measures ويعرضها.

## 8. الحالة الحالية المثبتة

آخر حالة تحقق ناجحة:

- dbt full build: `421/421 PASS`, بدون warnings أو errors.
- ERPNext raw journals: `858` صفًا، من يناير إلى أكتوبر 2026.
- actuals المطابقة لحساب `COST-OF-GOODS-SOLD-FDD`: `107` صفوف بقيمة مدين
  إجمالية `1,391,343.00 USD`.
- actuals الشهرية الموجودة: يناير، فبراير، مارس، أبريل، يوليو، أكتوبر.
- Cube يعيد group وbranch dimensions.
- Angular diagnostics بلا أخطاء.
- Dashboard يبنى داخل Docker ويعمل على `http://localhost:14200/`.

ملاحظة مهمة: snapshot ERPNext الحالي يحتوي posting date في أكتوبر، بما فيه
`2026-10-28`، رغم أن تاريخ السياق الحالي هو `2026-09-21`. إذا كان التقرير
يجب أن يمثل actuals حتى تاريخ اليوم فقط، أضف cutoff واضحًا مثل
`posting_date <= current_date` أو parameter مؤرخًا. لا تحذف البيانات المصدرية
لمجرد أنها مستقبلية.

## 9. القيود المفتوحة

### أ. budget غير مطابق لـ ERPNext

يجب تحميل أو إنشاء budget معتمد لنفس:

```text
ERP-FDD
COST-OF-GOODS-SOLD-FDD
العملة والفترة والفرع المناسب
```

لا تدّعِ أن report يعرض same-row Budget vs Actual قبل حل هذا التطابق.

### ب. branch ERPNext غير مربوط

كل قيود الحساب الحالي تقريبًا تحمل:

```text
source_cost_center_code = Main - FDD
```

ولا تحمل branch مستقلًا. لذلك `branch_id`/`branchCode` للـ ERPNext actual قد
يظهر فارغًا. الحل الصحيح هو ربط cost center بفرع في Django أو استيراد branch
فعلي من ERPNext إذا كان موجودًا، ثم إعادة بناء dbt. لا توزع المبلغ على AMM أو
أي فرع آخر بلا دليل مصدر.

### ج. future-dated actuals

افحص سياسة التقرير قبل إضافة cutoff. البيانات الحالية demo snapshot وليست
دفترًا إنتاجيًا.

### د. monthly budget allocation

التوزيع المتساوي مناسب لاختبار المارت، لكنه لا يمثل خطة شهرية واقعية. أضف
monthly budget lines أو allocation driver قبل استخدامه للتخطيط الإداري.

## 10. بروتوكول العمل لأي Agent جديد

قبل التعديل:

1. اقرأ `AI_CONTEXT.md` و`HANDOFF_TARGET_POSTGRES_ONLY.md`.
2. افحص `git status --short --branch` ولا تحذف تغييرات المستخدم.
3. حدد grain والمالك قبل تغيير SQL.
4. تحقق من مصدر actuals قبل لمس dashboard.

بعد تعديل dbt:

```bash
docker compose run --rm --no-deps dbt \
  dbt build --profiles-dir /root/.dbt --full-refresh
```

بعد تعديل Angular أو Cube:

```bash
docker compose up -d --build dashboard
docker compose logs --tail=100 dashboard
curl -fsS http://localhost:14200/ | wc -c
```

تحقق من Cube بعينة صغيرة:

```bash
curl -fsS --get 'http://localhost:14000/cubejs-api/v1/load' \
  --data-urlencode 'query={"measures":["BudgetVsActualMonth.actualAmount"],"dimensions":["BudgetVsActualMonth.monthKey","BudgetVsActualMonth.groupAccountCode"],"limit":10}'
```

لا تعتبر نجاح HTTP وحده نجاحًا ماليًا. تحقق أيضًا من المبالغ، الفترة، المصدر،
والـ grain.

## 11. Git والبيئة

المستودع الحالي يتتبع فرع `main` في:

```text
https://github.com/scerty/budgeting.git
```

ملف `.env` موجود في المستودع عمدًا لأن هذا stack تطوير محلي. لا تضع قيمه في
هذه الوثيقة ولا تنقلها إلى بيئة إنتاج. ملف `.gitignore` يستبعد فقط المخرجات
المولدة مثل dbt `target/logs` وPython caches وNode dependencies.

أي تغيير في secrets أو compose يجب أن يبقى متوافقًا مع `.env` و`dbt/profiles`.
لا ترفع بيانات إنتاج أو كلمات مرور حقيقية إلى هذا المستودع.