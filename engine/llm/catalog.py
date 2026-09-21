"""Semantic schema catalog used by the NL-to-SQL providers."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TABLES = {
    "gold.order_360": {
        "grain": "one resolved order",
        "columns": [
            "order_id", "customer_id", "order_date", "sales_channel", "store_id",
            "gross_merchandise_value", "discount_amount", "shipping_revenue",
            "captured_payment_amount", "refunded_amount", "net_revenue", "item_count",
            "unit_quantity", "order_status", "payment_status", "return_status",
            "promotion_count", "first_order_flag", "pipeline_run_id",
        ],
    },
    "gold.customer_daily": {
        "grain": "one customer per business date",
        "columns": [
            "customer_id", "metric_date", "order_count", "unit_quantity", "gross_revenue",
            "net_revenue", "refund_amount", "return_count", "support_contacts",
            "active_channel", "new_customer_flag", "repeat_customer_flag", "pipeline_run_id",
        ],
    },
    "gold.product_daily": {
        "grain": "one product per business date",
        "columns": [
            "product_id", "metric_date", "active_category", "units_sold", "order_count",
            "gross_revenue", "net_revenue", "refunded_units", "available_inventory",
            "reserved_inventory", "stockout_flag", "promotion_count", "pipeline_run_id",
        ],
    },
    "gold.channel_campaign_daily": {
        "grain": "one date, sales channel, and campaign",
        "columns": [
            "metric_date", "sales_channel", "campaign_id", "campaign_spend",
            "attributed_orders", "attributed_customers", "gross_revenue", "net_revenue",
            "refunds", "roas", "conversion_rate", "pipeline_run_id",
        ],
    },
    "gold.executive_kpis_daily": {
        "grain": "one business date",
        "columns": [
            "metric_date", "total_orders", "gross_revenue", "net_revenue",
            "average_order_value", "refund_rate", "return_rate", "repeat_customer_rate",
            "stockout_rate", "active_customers", "support_contact_rate",
            "data_freshness_utc", "pipeline_run_id",
        ],
    },
}

METRIC_DEFINITIONS = [
    "net_revenue is gross revenue minus discounts plus shipping revenue minus completed refunds.",
    "refund_rate is refunded orders divided by orders with captured payment.",
    "return_rate is returned orders divided by resolved orders.",
    "ROAS by campaign is SUM(net_revenue) / NULLIF(SUM(campaign_spend), 0), grouped by campaign_id unless a more detailed grain is explicitly requested; exclude groups with no campaign spend when ranking campaigns.",
    "daily executive metrics should use gold.executive_kpis_daily when the requested metric exists there.",
]


def schema_description() -> str:
    lines = ["Only query the following analytical tables:"]
    for table_name, definition in TABLES.items():
        lines.append(f"- {table_name} ({definition['grain']}): {', '.join(definition['columns'])}")
    lines.append("\nMetric definitions and aggregation rules:")
    lines.extend(f"- {definition}" for definition in METRIC_DEFINITIONS)
    return "\n".join(lines)


def catalog_path() -> Path:
    return PROJECT_ROOT / "engine" / "llm" / "schema_catalog.yaml"
