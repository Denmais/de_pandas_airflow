

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id      BIGINT PRIMARY KEY,
    signup_ts        TIMESTAMPTZ,
    country          TEXT,
    email            TEXT,
    is_active        BOOLEAN,
    loaded_at        TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fct_order (
    order_id         BIGINT PRIMARY KEY,
    customer_id      BIGINT,
    created_at       TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ,
    status           TEXT,
    amount_eur       NUMERIC(14,2),
    discount_eur     NUMERIC(14,2),
    net_amount_eur   NUMERIC(14,2),
    loaded_at        TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fct_event (
    event_id         TEXT PRIMARY KEY,
    customer_id      BIGINT,
    event_ts         TIMESTAMPTZ,
    event_type       TEXT,
    order_id         BIGINT NULL,
    source           TEXT,
    loaded_at        TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mart_daily_sales (
    dt                  DATE PRIMARY KEY,
    paid_orders          BIGINT NOT NULL,
    unique_buyers        BIGINT NOT NULL,
    gross_revenue_eur    NUMERIC(16,2) NOT NULL,
    net_revenue_eur      NUMERIC(16,2) NOT NULL,
    avg_order_value_eur  NUMERIC(16,2),
    refund_rate          NUMERIC(10,4),
    updated_at           TIMESTAMPTZ DEFAULT now()
);
