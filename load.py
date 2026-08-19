from sqlalchemy import create_engine, text
from starter_pandas import clean_customers, clean_orders
from pathlib import Path
import pandas as pd
from sqlalchemy import text
import pandas as pd


def load_customers(
    customers: pd.DataFrame,
    engine,
) -> None:

    with engine.begin() as conn:

        # Настоящая PostgreSQL temporary table.
        # Существует только внутри текущего соединения.
        conn.execute(text("""
            CREATE TEMP TABLE temp_cust (
                customer_id BIGINT,
                signup_ts TIMESTAMPTZ,
                country TEXT,
                email TEXT,
                is_active BOOLEAN
            )
            ON COMMIT DROP;
        """))

        customers.to_sql("temp_cust", conn, if_exists="append", index=False)

        conn.execute(text("""
            INSERT INTO dim_customer (
                customer_id,
                signup_ts,
                country,
                email,
                is_active
            )
            SELECT
                customer_id,
                signup_ts,
                country,
                email,
                is_active
            FROM temp_cust

            ON CONFLICT (customer_id)
            DO UPDATE SET
                signup_ts = EXCLUDED.signup_ts,
                country = EXCLUDED.country,
                email = EXCLUDED.email,
                is_active = EXCLUDED.is_active;
        """))


def load_orders(
    orders: pd.DataFrame,
    engine,
) -> None:

    with engine.begin() as conn:

        conn.execute(text("""
        CREATE TEMP TABLE IF NOT EXISTS temp_order (
            order_id         BIGINT PRIMARY KEY,
            customer_id      BIGINT,
            created_at       TIMESTAMPTZ,
            updated_at       TIMESTAMPTZ,
            status           TEXT,
            amount_eur       NUMERIC(14,2),
            discount_eur     NUMERIC(14,2),
            net_amount_eur   NUMERIC(14,2),
            loaded_at        TIMESTAMPTZ DEFAULT now()
            )
            ON COMMIT DROP;
        """))
        orders_to_load = orders[[
            "order_id",
            "customer_id",
            "created_at",
            "updated_at",
            "status",
            "amount_eur",
            "discount_eur",
            "net_amount_eur",
        ]]
        orders_to_load.to_sql("temp_order", conn, if_exists="append", index=False)

        conn.execute(text("""
            INSERT INTO fct_order (order_id, customer_id, created_at, updated_at, status, 
                          amount_eur, discount_eur, net_amount_eur, loaded_at)
            SELECT 
                          order_id,
                          customer_id,
                          created_at,
                          updated_at,
                          status,
                          amount_eur,
                          discount_eur,
                          net_amount_eur,
                          loaded_at
            FROM temp_order
            ON CONFLICT (order_id)
            DO UPDATE SET
                          customer_id=EXCLUDED.customer_id,
                          created_at=EXCLUDED.created_at,
                          updated_at=EXCLUDED.updated_at,
                          status=EXCLUDED.status,
                          amount_eur=EXCLUDED.amount_eur,
                          discount_eur=EXCLUDED.discount_eur,
                          net_amount_eur=EXCLUDED.net_amount_eur,
                          loaded_at=EXCLUDED.loaded_at
            WHERE EXCLUDED.updated_at>fct_order.updated_at;
        """))


if __name__ == "__main__":

    DATA_DIR = Path(__file__).parent / "data"
    engine = create_engine(
    "postgresql+psycopg2://postgres:123456@localhost:5433/postgres"
    )

    customers_raw = pd.read_csv(
        DATA_DIR / "customers.csv"
    )

    orders_raw = pd.read_csv(
        DATA_DIR / "orders.csv"
    )

    customers, _ = clean_customers(customers_raw)
    orders, _ = clean_orders(orders_raw, valid_customer_ids=customers["customer_id"],)
    load_customers(customers, engine)
    load_orders(orders, engine)
