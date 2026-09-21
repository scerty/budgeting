# سياق التسليم: الستاك البديل بدون Airbyte وClickHouse

## الغرض

هذه الوثيقة مخصصة لـ Agent آخر سيبني مسارًا بديلًا مرحليًا يستغني عن Airbyte وClickHouse، مع الإبقاء على المفاهيم المفيدة:

- مصادر متعددة
- ingestion موحد
- PostgreSQL
- dbt
- semantic layer
- Angular وPower BI لاحقًا

لا تفترض أن الستاك القديم يجب أن يستمر. المطلوب بناء مسار مستقل وواضح يمكن تشغيله محليًا، مع إبقاء العقد المنطقية قابلة للترقية لاحقًا.

## الهدف المعماري

```text
REST API / ERP / CSV / Excel
            ↓
Django Workers / Source Adapters
            ↓
PostgreSQL raw / landing
            ↓
 dbt staging / intermediate / gold
            ↓
PostgreSQL analytics
            ↓
Cube.js أو Semantic Layer بديل
            ↓
Angular / Power BI
```

في هذه المرحلة:

```text
Airbyte: خارج المسار التشغيلي
ClickHouse: خارج المسار التشغيلي
```

لا تحذف الستاك القديم أو ملفاته إلا إذا طلب المستخدم ذلك صراحة. يمكن إبقاؤه كمرجع ومقارنة، لكن المسار الجديد يجب ألا يعتمد عليه.

## قرار التصميم

PostgreSQL سيستضيف مرحليًا:

```text
تشغيل التطبيق
raw/landing ingestion
staging/intermediate dbt
analytics Gold
```

يفضل الفصل باستخدام schemas أو naming واضح:

```text
app أو public       جداول Django التشغيلية
raw                 السجلات الخام من المصادر الخارجية
analytics           النماذج التحليلية التي يبنيها dbt
```

إذا كان فصل schemas في dbt سيزيد التعقيد، استخدم convention واضحًا مؤقتًا، لكن لا تخلط مصدرًا خارجيًا مباشرة مع جدول Django التشغيلي دون سبب.

## مبادئ مهمة

### 1. لا تبنِ على افتراض أن كل مصدر يملك updated_at

كل مصدر يملك قدرات مختلفة:

```text
REST API: قد يملك cursor أو pagination
ERP: قد يملك updated_at أو CDC أو لا شيء
CSV/Excel: غالبًا snapshot فقط
نظام قديم: قد لا يملك timestamps أو delete events
```

يجب توثيق Source Capability Matrix لكل مصدر:

| المصدر | CDC | Cursor | updated_at | الحذف | الاستراتيجية |
|---|---:|---:|---:|---:|---|
| Django/PostgreSQL | ممكن | ممكن | نعم | soft delete أو CDC | cursor/incremental |
| REST API | حسب API | حسب API | حسب API | غالبًا غير واضح | cursor/snapshot |
| ERP | حسب الموصل | حسب النظام | تحقق | تحقق | حسب المصدر |
| CSV/Excel | لا | لا | غالبًا لا | غير معروف | snapshot + hash |

### 2. وحّد metadata قبل التحليل

كل سجل ingestion خارجي يجب أن يملك أو يرتبط بـ:

```text
source_system
source_entity أو source_table
source_record_id
ingested_at
record_hash
source_created_at      اختياري
source_updated_at      اختياري
is_deleted             أو deleted_at إذا كانت الاستراتيجية تدعم ذلك
```

هذه metadata ليست بديلًا عن source_updated_at، لكنها تجعل المصدر قابلًا للتتبع وتساعد في idempotency والتشخيص.

### 3. لا تضع منطق كل مصدر في dbt

يجب أن تكون مسؤولية Workers/Adapters:

```text
الاتصال بالمصدر
pagination
authentication
تحويل أولي للأنواع
upsert أو snapshot
تسجيل metadata
retry
```

ويجب أن تكون مسؤولية dbt:

```text
تنظيف تحليلي
توحيد schema
business joins
dimensions/facts/marts
اختبارات الجودة
```

## مكونات المسار الجديد

### A. Django Workers

ابدأ بمكوّن بسيط، ويمكن أن يكون Django management command أو worker مستقلًا.

أمثلة مستقبلية:

```bash
python manage.py ingest_source --source accounting_api
python manage.py ingest_source --source csv --file /path/file.csv
```

لا تبدأ بـ Celery أو broker معقد إلا عند الحاجة. الهدف الأول فهم دورة ingestion وidempotency.

كل adapter يجب أن يجيب عن:

```text
كيف يجلب البيانات؟
ما مفتاح المصدر؟
هل يستطيع معرفة الجديد؟
هل يستطيع معرفة التعديل؟
هل يستطيع معرفة الحذف؟
هل يعمل append أو upsert أو snapshot؟
```

### B. PostgreSQL raw/landing

يفضل إنشاء جداول raw منفصلة عن نماذج Django التطبيقية.

مثال منطقي لمصدر مصاريف:

```text
raw_expenses
------------
id
source_system
source_record_id
amount
currency
expense_date
description
department_id
source_created_at
source_updated_at
ingested_at
record_hash
is_deleted
```

المفتاح المنطقي المقترح:

```text
(source_system, source_record_id)
```

وليس `id` وحده، لأن مصدرين مختلفين قد يستخدمان نفس الأرقام.

### C. dbt على PostgreSQL

أنشئ profile باستخدام `dbt-postgres` بدل `dbt-clickhouse`.

المسار المقترح:

```text
raw -> stg -> int -> analytics Gold
```

النماذج التعليمية المستهدفة:

```text
stg_expenses
stg_branches
stg_departments
int_expenses_enriched
dim_branch
dim_department
dim_date
fact_expenses
expenses_by_branch
expenses_by_month
expenses_by_branch_month
```

حافظ على grain الواضح:

```text
fact_expenses:
  صف واحد لكل source_system + source_record_id

expenses_by_branch_month:
  صف واحد لكل branch_id + month_key
```

### D. Cube.js

اجعل Cube يقرأ من PostgreSQL analytics، وليس من raw أو جداول Django مباشرة.

يمكن الحفاظ على أسماء Cubes الحالية إذا كانت مناسبة:

```text
ExpensesByBranch
ExpensesByMonth
ExpensesByBranchMonth
```

الهدف أن تبقى Angular وPower BI منفصلتين عن تفاصيل ingestion.

### E. Angular

الواجهة الحالية يمكن إعادة استخدامها كمستهلك للـ Cube، لكن يجب تحديث endpoint/config حسب المسار الجديد.

لا تجعل Angular مسؤولًا عن:

```text
جلب المصادر الخارجية
التجميع business logic
إزالة التكرار
```

Angular يطلب measures/dimensions/filters من semantic layer فقط.

## Refresh Contract الجديد

الـ refresh لم يختفِ، لكنه أصبح:

```text
Ingestion refresh
    ↓
Incremental dbt refresh أو full batch حسب المصدر
    ↓
اختبارات dbt
    ↓
Cube cache refresh/invalidation
    ↓
Angular/Power BI يقرأ النتائج الجديدة
```

في البداية يمكن أن يكون التشغيل يدويًا لتعلم الفشل والنجاح. بعد التحقق، أضف scheduling عبر Cron أو systemd timer أو worker scheduler.

لا تشغل Full rebuild لكل تغيير صغير في التصميم النهائي. لكن لا تحوّل النماذج إلى Incremental قبل فهم:

- unique key
- update detection
- delete handling
- affected partitions
- backfill
- recovery/full refresh

## استراتيجية Incremental المستهدفة

ابدأ بـ `fact_expenses` فقط.

المطلوب:

```text
unique_key = source_system + source_record_id
```

واستخدم `source_updated_at` عندما يقدمه المصدر، وإلا استخدم استراتيجية المصدر المناسبة:

```text
append-only -> id أو cursor
snapshot -> مقارنة hash
لا metadata -> snapshot/full refresh
```

بالنسبة لـ `expenses_by_branch_month`، لا تضف صفًا أعمى عند كل تغيير. حدد affected partitions مثل:

```text
branch_id + month_key
```

ثم أعد حساب الأجزاء المتأثرة فقط، أو استخدم استراتيجية incremental مناسبة لـ PostgreSQL إذا كانت أبسط وأكثر موثوقية.

Full refresh يبقى متاحًا كـ recovery command عند:

```text
تغيير منطق model
إعادة backfill تاريخي
فقدان state
تصحيح ingestion
تغيير mapping
```

## حالات الاختبار الإلزامية

لكل adapter ومسار البيانات اختبر:

### INSERT

```text
إضافة سجل جديد
-> تشغيل ingestion
-> التأكد من ظهوره مرة واحدة
```

### UPDATE

```text
تعديل سجل موجود
-> تشغيل ingestion
-> التأكد من عدم وجود نسخة تحليلية مكررة
-> التأكد من تغير الإجمالي الصحيح
```

### DELETE

```text
حذف أو إلغاء سجل
-> معرفة هل المصدر يدعم delete event
-> إن لم يدعم، اختيار soft delete أو snapshot comparison
```

### Retry

```text
تشغيل نفس ingestion مرتين
-> لا تتضاعف السجلات
-> يبقى نفس logical key
```

### Partial failure

```text
فشل المصدر أو dbt
-> لا تعلن الدورة نجاحًا
-> لا تنشر بيانات Gold غير مختبرة
```

### Full recovery

```text
dbt build --full-refresh
```

يجب أن يعيد النتيجة الصحيحة بعد تلف أو تغيير incremental state.

## ترتيب التنفيذ المقترح للـ Agent الجديد

1. قراءة هذا الملف وملف `HANDOFF_CURRENT_AIRBYTE_CLICKHOUSE.md` للمقارنة فقط.
2. عدم تعديل الستاك القديم في البداية.
3. فحص PostgreSQL وDjango الحاليين.
4. إنشاء target schemas أو raw tables في PostgreSQL.
5. تصميم adapter واحد فقط، ويفضل CSV أو مصدر Django تجريبي.
6. إضافة source metadata وlogical key وrecord hash.
7. تنفيذ ingestion idempotent.
8. إنشاء مشروع dbt-postgres بسيط.
9. بناء `stg_expenses` ثم `fact_expenses`.
10. إضافة tests قبل Gold marts.
11. بناء `expenses_by_branch_month` واختبار grain المركب.
12. ربط Cube.js بPostgreSQL analytics.
13. إعادة ربط Angular واختبار branch/month filters.
14. إضافة INSERT ثم UPDATE ثم DELETE tests.
15. إضافة orchestration/scheduling فقط بعد نجاح التشغيل اليدوي.

## معايير نجاح المسار البديل

يعتبر المسار الجديد ناجحًا عندما:

```text
لا يعتمد على Airbyte
لا يعتمد على ClickHouse
يقبل مصدرًا واحدًا على الأقل عبر adapter
يمنع تكرار السجلات عند إعادة التشغيل
يميز المصدر ومفتاح السجل
يمرر metadata إلى dbt
ينتج fact وGold على PostgreSQL
يمر Cube من PostgreSQL
تعمل Angular filters
dbt tests تمر
يوجد full recovery path
```

## أسلوب العمل المطلوب

المستخدم يتعلم تدريجيًا. لا تبنِ كل النظام دفعة واحدة.

في كل مرحلة:

```text
اشرح المفهوم بالعربية
حدد فرضية صغيرة
نفذ أقل تعديل ممكن
شغّل تحققًا مركزًا
اشرح النتيجة
ثم انتقل للخطوة التالية
```

لا تكتب كودًا كبيرًا دون شرح. لا تضف مكتبات أو خدمات مثل Celery/Redis/Airflow قبل إثبات الحاجة. الهدف هو فهم المعمارية، وليس استبدال التعقيد القديم بتعقيد جديد.

## القرار النهائي للمرحلة

المسار المستهدف حاليًا:

```text
Django Workers / Adapters
    -> PostgreSQL raw
    -> dbt-postgres
    -> PostgreSQL analytics
    -> Cube.js
    -> Angular / Power BI
```

Airbyte وClickHouse مؤجلان، وليسَا ملغيين نهائيًا. يمكن إعادتهما لاحقًا عندما تظهر حاجة فعلية مثل كثرة الموصلات أو أحجام تحليلية كبيرة.
