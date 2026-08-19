from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"


def clean_customers(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    df = df.copy()

    # -------------------------
    # 1. Normalization
    # -------------------------

    df["customer_id"] = (pd.to_numeric(df["customer_id"], errors="coerce"))

    df["signup_ts"] = pd.to_datetime(df["signup_ts"], errors="coerce", utc=True)

    df["country"] = (
        df["country"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["email"] = (
        df["email"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    df["is_active"] = df["is_active"].astype("boolean")

    # -------------------------
    # 2. Validation
    # -------------------------

    invalid_customer_id = df["customer_id"].isna()
    invalid_signup_ts = df["signup_ts"].isna()

    df["reject_reason"] = pd.NA

    df.loc[
        invalid_customer_id,
        "reject_reason"
    ] = "invalid_customer_id"

    df.loc[
        df["reject_reason"].isna()
        & invalid_signup_ts,
        "reject_reason"
    ] = "invalid_signup_ts"

    # -------------------------
    # 3. Split
    # -------------------------

    reject_df = df[
        df["reject_reason"].notna()
    ].copy()

    clean_df = df[
        df["reject_reason"].isna()
    ].copy()

    # -------------------------
    # 4. Deduplication
    # -------------------------

    clean_df = (
        clean_df
        .drop_duplicates(
            subset=["customer_id"],
            keep="last",
        )
        .drop(columns=["reject_reason"])
        .reset_index(drop=True)
    )

    reject_df = reject_df.reset_index(drop=True)

    return clean_df, reject_df


def clean_orders(
    df: pd.DataFrame,
    valid_customer_ids,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    df = df.copy()

    # -------------------------
    # 1. Normalization
    # -------------------------

    df["customer_id"] = (
        pd.to_numeric(df["customer_id"], errors="coerce")
        .astype("Int64")
    )

    df["order_id"] = (
        pd.to_numeric(df["order_id"], errors="coerce")
        .astype("Int64")
    )

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce",
        utc=True,
    )

    df["updated_at"] = pd.to_datetime(
        df["updated_at"],
        errors="coerce",
        utc=True,
    )

    df["status"] = (
        df["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    df["currency"] = (
        df["currency"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce",
    )

    df["discount"] = pd.to_numeric(
        df["discount"],
        errors="coerce",
    )

    # -------------------------
    # 2. CDC deduplication
    # -------------------------
    #
    # Если order_id повторяется,
    # берём самую новую версию записи.
    #

    df = (
        df
        .sort_values(
            by=["order_id", "updated_at"],
            na_position="first",
        )
        .drop_duplicates(
            subset=["order_id"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # -------------------------
    # 3. Validation
    # -------------------------

    valid_statuses = {
        "paid",
        "shipped",
        "cancelled",
        "refunded",
    }

    valid_currencies = {
        "EUR",
        "PLN",
    }

    invalid_customer_id = df["customer_id"].isna()

    orphan_customer = (
        df["customer_id"].notna()
        & ~df["customer_id"].isin(valid_customer_ids)
    )

    invalid_order_id = df["order_id"].isna()

    invalid_created_at = df["created_at"].isna()

    invalid_updated_at = df["updated_at"].isna()

    invalid_status = (
        df["status"].isna()
        | ~df["status"].isin(valid_statuses)
    )

    invalid_amount = (
        df["amount"].isna()
        | (df["amount"] <= 0)
    )

    invalid_discount = (
        df["discount"].isna()
        | (df["discount"] < 0)
        | (df["discount"] > df["amount"])
    )

    invalid_currency = (
        df["currency"].isna()
        | ~df["currency"].isin(valid_currencies)
    )

    df["reject_reason"] = pd.NA

    # Здесь порядок = приоритет ошибки

    df.loc[
        invalid_order_id,
        "reject_reason"
    ] = "invalid_order_id"

    df.loc[
        df["reject_reason"].isna()
        & invalid_customer_id,
        "reject_reason"
    ] = "invalid_customer_id"

    df.loc[
        df["reject_reason"].isna()
        & orphan_customer,
        "reject_reason"
    ] = "orphan_customer_id"

    df.loc[
        df["reject_reason"].isna()
        & invalid_created_at,
        "reject_reason"
    ] = "invalid_created_at"

    df.loc[
        df["reject_reason"].isna()
        & invalid_updated_at,
        "reject_reason"
    ] = "invalid_updated_at"

    df.loc[
        df["reject_reason"].isna()
        & invalid_status,
        "reject_reason"
    ] = "invalid_status"

    df.loc[
        df["reject_reason"].isna()
        & invalid_amount,
        "reject_reason"
    ] = "invalid_amount"

    df.loc[
        df["reject_reason"].isna()
        & invalid_discount,
        "reject_reason"
    ] = "invalid_discount"

    df.loc[
        df["reject_reason"].isna()
        & invalid_currency,
        "reject_reason"
    ] = "invalid_currency"

    # -------------------------
    # 4. Split
    # -------------------------

    reject_df = df[
        df["reject_reason"].notna()
    ].copy()

    clean_df = df[
        df["reject_reason"].isna()
    ].copy()

    # -------------------------
    # 5. Currency conversion
    # -------------------------

    exchange_rates = {
        "EUR": 1.0,
        "PLN": 0.23,
    }

    clean_df["exchange_rate"] = (
        clean_df["currency"]
        .map(exchange_rates)
    )

    clean_df["amount_eur"] = (
        clean_df["amount"]
        * clean_df["exchange_rate"]
    ).round(2)

    clean_df["discount_eur"] = (
        clean_df["discount"]
        * clean_df["exchange_rate"]
    ).round(2)

    clean_df["net_amount_eur"] = (
        clean_df["amount_eur"]
        - clean_df["discount_eur"]
    ).round(2)

    clean_df = (
        clean_df
        .drop(columns=[
            "reject_reason",
            "exchange_rate",
        ])
        .reset_index(drop=True)
    )

    reject_df = reject_df.reset_index(drop=True)

    return clean_df, reject_df


def clean_events(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    df = df.copy()

    # -------------------------
    # 1. Remove exact duplicates
    # -------------------------

    df = (
        df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Сохраняем информацию:
    # был ли order_id указан в raw-данных.
    #
    # Это нужно, чтобы отличить настоящий NULL
    # от значения "not_an_order".
    raw_order_present = (
        df["order_id"]
        .astype("string")
        .str.strip()
        .notna()
    )

    # -------------------------
    # 2. Normalization
    # -------------------------

    # event_id строковый!
    df["event_id"] = (
        df["event_id"]
        .astype("string")
        .str.strip()
    )

    df["customer_id"] = (
        pd.to_numeric(
            df["customer_id"],
            errors="coerce",
        )
        .astype("Int64")
    )

    df["event_ts"] = pd.to_datetime(
        df["event_ts"],
        errors="coerce",
        utc=True,
    )

    df["event_type"] = (
        df["event_type"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    df["order_id"] = (
        pd.to_numeric(
            df["order_id"],
            errors="coerce",
        )
        .astype("Int64")
    )

    df["source"] = (
        df["source"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    # -------------------------
    # 3. Validation
    # -------------------------

    valid_event_types = {
        "view_product",
        "add_to_cart",
        "checkout_started",
        "purchase",
    }

    invalid_event_id = (
        df["event_id"].isna()
        | (df["event_id"] == "")
    )

    invalid_customer_id = (
        df["customer_id"].isna()
    )

    invalid_event_ts = (
        df["event_ts"].isna()
    )

    invalid_event_type = (
        df["event_type"].isna()
        | ~df["event_type"].isin(valid_event_types)
    )

    # Если raw order_id был заполнен,
    # но после pd.to_numeric получил NA —
    # значит там было мусорное значение.
    invalid_order_id = (
        raw_order_present
        & df["order_id"].isna()
    )

    df["reject_reason"] = pd.NA

    df.loc[
        invalid_event_id,
        "reject_reason"
    ] = "invalid_event_id"

    df.loc[
        df["reject_reason"].isna()
        & invalid_customer_id,
        "reject_reason"
    ] = "invalid_customer_id"

    df.loc[
        df["reject_reason"].isna()
        & invalid_event_ts,
        "reject_reason"
    ] = "invalid_event_ts"

    df.loc[
        df["reject_reason"].isna()
        & invalid_event_type,
        "reject_reason"
    ] = "invalid_event_type"

    df.loc[
        df["reject_reason"].isna()
        & invalid_order_id,
        "reject_reason"
    ] = "invalid_order_id"

    # -------------------------
    # 4. Split
    # -------------------------

    reject_df = df[
        df["reject_reason"].notna()
    ].copy()

    clean_df = df[
        df["reject_reason"].isna()
    ].copy()

    # event_id = business key
    clean_df = (
        clean_df
        .drop_duplicates(
            subset=["event_id"],
            keep="last",
        )
        .drop(columns=["reject_reason"])
        .reset_index(drop=True)
    )

    reject_df = reject_df.reset_index(drop=True)

    return clean_df, reject_df


def build_daily_sales(orders: pd.DataFrame) -> pd.DataFrame:

    df = orders.copy()
    df["dt"] = df["created_at"].dt.date
    df["is_paid"] = df["status"].eq("paid")

    daily = (
        df.groupby("dt")
            .apply(
                lambda x: pd.Series({
                "paid_orders": x["is_paid"].sum(),

              "unique_buyers": x.loc[
                  x["is_paid"], "customer_id"
              ].nunique(),

              "gross_revenue_eur": x.loc[
                  x["is_paid"], "amount_eur"
              ].sum(),

              "net_revenue_eur": x.loc[
                  x["is_paid"], "net_amount_eur"
              ].sum(),

              "avg_order_value_eur": x.loc[
                  x["is_paid"], "net_amount_eur"
              ].mean(),
              "refund_rate": (
                  x["status"].eq("refunded").sum()
                  / len(x)
              ),
          })
      )
      .reset_index()
    )

    return daily


if __name__ == "__main__":

    customers_raw = pd.read_csv(
        DATA_DIR / "customers.csv"
    )

    orders_raw = pd.read_csv(
        DATA_DIR / "orders.csv"
    )

    events_raw = pd.read_csv(
        DATA_DIR / "events.csv"
    )

    customers, customers_rejects = clean_customers(
        customers_raw
    )

    orders, orders_rejects = clean_orders(
        orders_raw,
        valid_customer_ids=customers["customer_id"],
    )

    events, events_rejects = clean_events(
        events_raw
    )

    print("CUSTOMERS")
    print("clean:", len(customers))
    print("rejects:", len(customers_rejects))

    print("\nORDERS")
    print("clean:", len(orders))
    print("rejects:", len(orders_rejects))

    print("\nEVENTS")
    print("clean:", len(events))
    print("rejects:", len(events_rejects))

    print("\nORDER REJECT REASONS")
    print(
        orders_rejects["reject_reason"]
        .value_counts()
    )

    print("\nEVENT REJECT REASONS")
    print(
        events_rejects["reject_reason"]
        .value_counts()
    )

    daily_sales = build_daily_sales(orders)
