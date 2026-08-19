# Подсказки

Открывай по уровням. Не читай всё сразу, если хочешь сохранить сложность.

## Level 1 — pandas

- Для timestamp посмотри на `pd.to_datetime(..., errors="coerce", utc=True)`.
- Для текстовых полей пригодятся `.str.strip()` и `.str.lower()`.
- Для latest-row-per-key: сначала корректно распарсь `updated_at`, потом подумай про `sort_values + drop_duplicates`.
- Rejects удобно собирать булевыми масками.
- Для nullable integer в pandas посмотри dtype `Int64`.

## Level 2 — pandas

У заказа может быть несколько причин rejection.
Есть два подхода:

- приоритетная причина;
- строка со списком причин.

Для упражнения достаточно приоритетной причины, если ты явно документируешь порядок.

Не забудь, что `NaN`, `None` и `NaT` ведут себя по-разному.

## Level 3 — PostgreSQL

Для idempotent загрузки подумай про:

```sql
INSERT ... ON CONFLICT (...) DO UPDATE
```

Для order CDC условие обновления можно поместить в `WHERE` секцию `DO UPDATE`.

Для bulk load эффективнее:
1. загрузить во staging;
2. выполнить SQL merge/upsert;
3. очистить staging.

## Level 4 — Airflow

Главная идея:

```python
def task_fn(data_interval_start=None, data_interval_end=None, **context):
    ...
```

Фильтруй данные по интервалу DAG run, а не по текущему системному времени.

Большой DataFrame не надо возвращать из task.
Лучше передавать:
- имя partition;
- путь к файлу;
- row count;
- run_id.

## Level 5 — DQ

Проверка должна быть формализована как условие.

Плохо:

> "revenue выглядит нормально"

Лучше:

```text
net_revenue_eur >= 0
duplicate_order_count = 0
orphan_customer_count = 0
```

Для production-подхода разделяй:
- hard fail;
- warning;
- anomaly.

## Level 6 — Архитектура

Хороший pipeline может выглядеть так:

```text
raw csv
   |
   v
pandas validation
   |
   +--> rejects
   |
   v
postgres staging
   |
   v
upsert core tables
   |
   v
sql mart
   |
   v
data quality
```

Если хочешь усложнить задачу, сделай так, чтобы rerun одного Airflow task
не требовал полного перезапуска DAG.
