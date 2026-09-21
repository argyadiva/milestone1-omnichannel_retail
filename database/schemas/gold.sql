CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS gold.order_360 (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date DATE NOT NULL,
    sales_channel TEXT NOT NULL,
    store_id TEXT,
    gross_merchandise_value NUMERIC(14, 2) NOT NULL,
    discount_amount NUMERIC(14, 2) NOT NULL,
    shipping_revenue NUMERIC(14, 2) NOT NULL,
    captured_payment_amount NUMERIC(14, 2) NOT NULL,
    refunded_amount NUMERIC(14, 2) NOT NULL,
    net_revenue NUMERIC(14, 2) NOT NULL,
    item_count INTEGER NOT NULL,
    unit_quantity INTEGER NOT NULL,
    order_status TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    return_status TEXT NOT NULL,
    promotion_count INTEGER NOT NULL,
    first_order_flag BOOLEAN NOT NULL,
    pipeline_run_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.customer_daily (
    customer_id TEXT NOT NULL,
    metric_date DATE NOT NULL,
    order_count INTEGER NOT NULL,
    unit_quantity INTEGER NOT NULL,
    gross_revenue NUMERIC(14, 2) NOT NULL,
    net_revenue NUMERIC(14, 2) NOT NULL,
    refund_amount NUMERIC(14, 2) NOT NULL,
    return_count INTEGER NOT NULL,
    support_contacts INTEGER NOT NULL,
    active_channel TEXT,
    new_customer_flag BOOLEAN NOT NULL,
    repeat_customer_flag BOOLEAN NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    PRIMARY KEY (customer_id, metric_date)
);

CREATE TABLE IF NOT EXISTS gold.product_daily (
    product_id TEXT NOT NULL,
    metric_date DATE NOT NULL,
    active_category TEXT,
    units_sold INTEGER NOT NULL,
    order_count INTEGER NOT NULL,
    gross_revenue NUMERIC(14, 2) NOT NULL,
    net_revenue NUMERIC(14, 2) NOT NULL,
    refunded_units INTEGER NOT NULL,
    available_inventory INTEGER,
    reserved_inventory INTEGER,
    stockout_flag BOOLEAN,
    promotion_count INTEGER NOT NULL,
    pipeline_run_id TEXT NOT NULL,
    PRIMARY KEY (product_id, metric_date)
);

CREATE TABLE IF NOT EXISTS gold.channel_campaign_daily (
    metric_date DATE NOT NULL,
    sales_channel TEXT NOT NULL,
    campaign_id TEXT NOT NULL,
    campaign_spend NUMERIC(14, 2) NOT NULL,
    attributed_orders INTEGER NOT NULL,
    attributed_customers INTEGER NOT NULL,
    gross_revenue NUMERIC(14, 2) NOT NULL,
    net_revenue NUMERIC(14, 2) NOT NULL,
    refunds NUMERIC(14, 2) NOT NULL,
    roas NUMERIC(14, 4),
    conversion_rate NUMERIC(14, 4),
    pipeline_run_id TEXT NOT NULL,
    PRIMARY KEY (metric_date, sales_channel, campaign_id)
);

CREATE TABLE IF NOT EXISTS gold.executive_kpis_daily (
    metric_date DATE PRIMARY KEY,
    total_orders INTEGER NOT NULL,
    gross_revenue NUMERIC(14, 2) NOT NULL,
    net_revenue NUMERIC(14, 2) NOT NULL,
    average_order_value NUMERIC(14, 2) NOT NULL,
    refund_rate NUMERIC(14, 4) NOT NULL,
    return_rate NUMERIC(14, 4) NOT NULL,
    repeat_customer_rate NUMERIC(14, 4) NOT NULL,
    stockout_rate NUMERIC(14, 4) NOT NULL,
    active_customers INTEGER NOT NULL,
    support_contact_rate NUMERIC(14, 4) NOT NULL,
    data_freshness_utc TIMESTAMPTZ NOT NULL,
    pipeline_run_id TEXT NOT NULL
);
