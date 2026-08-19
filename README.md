# DE Practice Project: Marketplace Daily Pipeline

## Сценарий

Ты работаешь Data Engineer в небольшом marketplace. Каждый день в object storage
появляются три сырых файла:

- `customers.csv`
- `orders.csv`
- `events.csv`

Нужно построить воспроизводимый batch-пайплайн:

**CSV -> pandas cleaning -> PostgreSQL -> daily mart -> Airflow orchestration**

Данные специально содержат ошибки, дубли и пограничные случаи.

---

## Бизнес-правила

### Customers

1. `customer_id` — бизнес-ключ.
2. Дубликаты по `customer_id` нужно схлопнуть.
3. `country` привести к uppercase.
4. `email` привести к lowercase и trim.
5. Невалидный `signup_ts` не должен ронять весь pipeline.

### Orders

1. `order_id` — бизнес-ключ.
2. Если один `order_id` встречается несколько раз, оставить запись с максимальным `updated_at`.
3. `status` привести к lowercase.
4. Валидные статусы: `paid`, `shipped`, `cancelled`, `refunded`.
5. `amount` должен быть > 0.
6. `discount` должен быть >= 0 и не больше `amount`.
7. Для упражнения считать:
   - `EUR -> EUR`: курс `1.0`
   - `PLN -> EUR`: курс `0.23`
8. Рассчитать:
   - `amount_eur`
   - `discount_eur`
   - `net_amount_eur = amount_eur - discount_eur`
9. Заказ с неизвестным `customer_id` не загружать в факт, а записать в reject/quarantine набор.

### Events

1. `event_id` — бизнес-ключ.
2. Удалить точные дубли.
3. `event_type` привести к lowercase.
4. Валидные типы:
   `view_product`, `add_to_cart`, `checkout_started`, `purchase`.
5. Невалидные timestamp/event_type отправлять в reject.
6. `order_id` должен быть nullable integer.

---

# Часть 1. pandas

Напиши функции:

```python
clean_customers(df) -> tuple[clean_df, reject_df]
clean_orders(df, valid_customer_ids) -> tuple[clean_df, reject_df]
clean_events(df) -> tuple[clean_df, reject_df]
```

Требования:

- Не использовать циклы по строкам.
- Применять vectorized operations.
- Явно работать с dtype.
- Timestamp привести к UTC.
- Код должен быть детерминированным.
- В reject добавить колонку `reject_reason`.

### Дополнительная задача

Собери дневную витрину в pandas:

| column | meaning |
|---|---|
| dt | день заказа |
| paid_orders | число заказов со status = paid |
| unique_buyers | уникальные покупатели paid-заказов |
| gross_revenue_eur | сумма amount_eur paid-заказов |
| net_revenue_eur | сумма net_amount_eur paid-заказов |
| avg_order_value_eur | средний net_amount_eur paid-заказа |
| refund_rate | refunded_orders / all_valid_orders |

---

# Часть 2. PostgreSQL

Загрузи очищенные данные в таблицы из `sql/schema.sql`.

## Требования

1. Загрузка должна быть **идемпотентной**.
2. Повторный запуск за тот же день не должен создавать дубли.
3. Для `fct_order` реализуй UPSERT:
   обновлять запись, только если входящий `updated_at`
   новее уже сохранённого.
4. Построй `mart_daily_sales` SQL-ом из `fct_order`.
5. Добавь индексы, которые считаешь полезными.

## SQL-задачи

Напиши запросы:

1. Top-10 клиентов по `net_revenue_eur`.
2. 7-day rolling revenue.
3. Conversion funnel по дням:
   `view_product -> add_to_cart -> checkout_started -> purchase`.
4. Доля клиентов, совершивших повторную покупку.
5. Найди дни, где revenue отличается от предыдущего дня более чем на 30%.

---

# Часть 3. Airflow

Доработай `airflow/de_marketplace_daily.py`.

Желаемый граф:

```text
                load_customers
              /                \
start ------                    ---- build_daily_mart ---- quality ---- finish
              \                /
                load_orders
                  |
                load_events
```

Можешь изменить зависимости, если предложишь более корректный вариант.

## Требования к DAG

- daily schedule;
- `catchup=True`;
- одна логическая дата = один partition/day;
- использовать logical date/data interval, а не `datetime.now()`;
- retries;
- идемпотентные task-и;
- не передавать большие DataFrame через XCom;
- ошибки quality checks должны падать task-ом.

---

# Data Quality Checks

Минимум 8 проверок. Например:

1. `customer_id` unique.
2. `order_id` unique.
3. `event_id` unique.
4. Нет отрицательных `amount_eur`.
5. `discount_eur <= amount_eur`.
6. Все `status` входят в whitelist.
7. В факте заказов нет orphan `customer_id`.
8. `mart_daily_sales.net_revenue_eur >= 0`.
9. Row count не упал более чем на X% день-к-дню.
10. Для закрытого дня витрина содержит ровно одну строку.

---

# Что считать хорошим решением

## Junior+
- чистка через pandas;
- таблицы созданы;
- данные загружаются;
- DAG запускается.

## Middle
- идемпотентность;
- UPSERT;
- rejects;
- адекватные индексы;
- partition-aware DAG;
- DQ checks.

## Middle+
- staging layer;
- транзакции;
- bulk insert / COPY;
- observability;
- retries без побочных эффектов;
- backfill;
- объяснение trade-offs.

---

# Stretch goals

1. Убрать pandas из aggregation step и считать mart целиком SQL-ом.
2. Сделать SCD2 для `customer.country`.
3. Добавить incremental load по `updated_at`.
4. Ввести таблицу `etl_run_log`.
5. Сделать SLA/alerting.
6. Переписать загрузку через `COPY`.
7. Контейнеризировать Postgres + Airflow через Docker Compose.

---

# Ограничение

В репозитории специально **нет готового решения**. Файлы `hints.md`
содержат подсказки от лёгких к более явным.
# de_pandas_airflow
