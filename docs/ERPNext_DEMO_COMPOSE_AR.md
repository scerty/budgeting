# ERPNext كمصدر بيانات تجريبي

يعمل ERPNext هنا كمصدر خارجي مستقل لنظام Finance Stack. قاعدة بيانات ERPNext هي MariaDB، ولا يتم ربطها مباشرة بقاعدة PostgreSQL؛ الاستهلاك اللاحق يكون عبر REST API.

## التشغيل

من جذر المشروع:

```bash
docker compose -f compose.erpnext.yml up -d
docker compose -f compose.erpnext.yml ps
```

يفتح ERPNext على:

```text
http://localhost:18080
```

بيانات الدخول المحلية:

```text
Administrator / admin
```

البيانات demo تنشئها خدمة `seed-demo` مرة واحدة، وتشمل Company وChart of Accounts وGL Entries وفواتير شراء ومبيعات وPayment Entries. هذه البيئة للاختبار المحلي فقط.

## اختبار REST

```bash
curl -fsS -c /tmp/erpnext.cookies \
  -H 'Content-Type: application/json' \
  -d '{"usr":"Administrator","pwd":"admin"}' \
  http://localhost:18080/api/method/login

curl -fsS -b /tmp/erpnext.cookies \
  'http://localhost:18080/api/resource/GL%20Entry?limit_page_length=5'
```

المسار الأول المقترح للـ ingestion هو `GL Entry` إلى `RawJournalLine`. بعد ذلك يمكن قراءة `Purchase Invoice` و`Sales Invoice` و`Payment Entry` مع الاحتفاظ بـ `voucher_type` و`voucher_no` و`source_payload`.

## استيراد GL Entry إلى Django

بعد تشغيل Finance Stack وERPNext، ينفذ الأمر التالي استيرادًا idempotent إلى `RawJournalLine`:

```bash
docker compose exec django python manage.py ingest_erpnext \
  --organization DEMO \
  --username Administrator \
  --password admin
```

القيمة الافتراضية للعنوان هي `http://host.docker.internal:18080`، ويُستحسن تمرير كلمة المرور عبر `ERPNEXT_PASSWORD` بدل كتابتها في shell. الأمر يسجل `ImportSource` و`IngestionRun`، ويقرأ الصفحات عبر REST، ويحفظ payload وhash وسلسلة المصدر. إعادة تشغيله تحدّث السجلات الموجودة ولا تنشئ نسخًا مكررة.

للتحقق من النتيجة:

```bash
docker compose exec django python manage.py shell -c \
  'from finance.models import RawJournalLine; print(RawJournalLine.objects.filter(source_system="erpnext").count())'
```

السجلات الملغاة تُستبعد افتراضيًا، ويمكن إدخالها مع وسم `is_deleted` باستخدام `--include-cancelled`.

## تكبير البيانات التجريبية

البيانات الافتراضية صغيرة. يوجد seeder إضافي في `erpnext_bulk_seed.py` ينشئ مستندات ERPNext حقيقية، وليس صفوف `GL Entry` مصطنعة:

```bash
docker compose -f compose.erpnext.yml exec backend \
  bench --site frontend execute erpnext.bulk_seed.run \
  --kwargs '{"sales_count":100,"purchase_count":100,"payment_count":200,"batch":"bulk-2026-09-21"}'
```

هذا المثال ينشئ 100 فاتورة مبيعات و100 فاتورة شراء و200 دفعة. كل مستند يستخدم عملاء وموردين وحسابات الشركة الموجودة، وتوضع له علامة batch تمنع التكرار عند إعادة الأمر. بعده شغّل `ingest_erpnext` مرة أخرى لاستيراد قيود `GL Entry` الجديدة إلى Django.

يمكن تجربة batch صغيرة أولًا:

```bash
docker compose -f compose.erpnext.yml exec backend \
  bench --site frontend execute erpnext.bulk_seed.run \
  --kwargs '{"sales_count":2,"purchase_count":2,"payment_count":4,"batch":"validation-2026-09"}'
```

هذه البيانات تجريبية فقط؛ لا تشغّل seeder على ERPNext إنتاجي.

## توليد ومزامنة الهيكل التنظيمي

لتوليد فروع ومراكز تكلفة للشركة التجريبية:

```bash
docker compose -f compose.erpnext.yml exec backend \
  bench --site frontend execute erpnext.bulk_seed.run_structure
```

ينشئ الأمر الفروع `AMM` و`IRB` و`AQB` ومراكز تكلفة بنفس الأسماء تحت الشركة `Finance Demo (Demo)`. الأمر idempotent، وإعادة تشغيله لا تنشئ نسخًا مكررة.

بعد ذلك تُزامن master data إلى Django:

```bash
docker compose exec django python manage.py sync_erpnext_master_data \
  --organization DEMO \
  --branch-company "Finance Demo (Demo)" \
  --username Administrator \
  --password admin
```

المزامنة تحول:

```text
ERPNext Company      -> LegalEntity
ERPNext Account      -> GroupAccount + EntityAccount
ERPNext Cost Center  -> CostCenter
ERPNext Branch       -> Branch
```

تُستخدم أكواد `ERP-FD` و`ERP-FDD` للكيانات القانونية القادمة من ERPNext، بينما تبقى بيانات Django التجريبية الحالية مثل `DEMO-JO` منفصلة.

## بناء مجموعة شركات متكاملة في Django

لإنشاء طبقة المجموعة والهيكل التشغيلي المرتبط بالفروع:

```bash
docker compose exec django python manage.py build_demo_group_structure
```

ينشئ الأمر:

```text
ERP-GROUP Finance Demo Group Holding
├── ERP-FD  Finance Demo                 (ملكية 100%)
└── ERP-FDD Finance Demo (Demo)          (ملكية 100%)
  ├── AMM / IRB / AQB
  ├── Finance / Human Resources / Operations / Sales / IT لكل فرع
  └── مركز تكلفة لكل قسم
```

كما ينشئ وحدات الأعمال `Shared Services` و`Commercial` و`Operations` ويربطها بالكيانات التابعة. الأمر idempotent ويمكن إعادة تشغيله دون تكرار. الأقسام تُدار في Django لأنها تدعم الربط المباشر بين القسم والفرع، وهو ربط غير موجود كحقل مستقل في ERPNext Department.

## تحويل قيود ERPNext باستخدام dbt

بعد استيراد القيود إلى Django، يبني dbt الطبقة التحليلية من جدول `finance_rawjournalline`:

```bash
docker compose run --rm --no-deps dbt \
  dbt build --profiles-dir /root/.dbt --full-refresh
```

النماذج الأساسية هي:

```text
analytics.stg_journal_lines
    -> analytics.fact_journal_lines
    -> analytics.dim_date
```

يحتوي `fact_journal_lines` على صف واحد لكل سطر قيد فعّال، مع الحساب والكيان ومركز التكلفة كما وردت من المصدر، إضافة إلى `debit_amount` و`credit_amount` و`signed_amount` و`date_key`. لا يحوّل هذا المسار القيود إلى مصروفات؛ `fact_expenses` يبقى مسارًا منفصلًا.

اختبارات dbt تتحقق من عدم التكرار، الحقول الإلزامية، كون القيد أحادي الجانب، وصحة علاقة التاريخ. في آخر تشغيل ناجح: 858 سطرًا، والمدين والدائن متساويان بقيمة `4,939,449.00`، ونجحت اختبارات المشروع كاملة.

الخطوة التالية هي إضافة نموذج Cube يقرأ `analytics.fact_journal_lines` ويعرض القيود حسب الشركة والحساب والفرع والقسم ومركز التكلفة. الربط التحليلي بين أكواد ERPNext النصية والـ master data التنظيمية سيأتي بعد تثبيت قواعد المطابقة.

## الإيقاف والتنظيف

لإيقاف الحاويات مع الاحتفاظ بالبيانات:

```bash
docker compose -f compose.erpnext.yml down
```

لحذف بيئة ERPNext التجريبية وبياناتها بالكامل:

```bash
docker compose -f compose.erpnext.yml down -v
```

لا تستخدم كلمة المرور التجريبية خارج بيئة محلية disposable.