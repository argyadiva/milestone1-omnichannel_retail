"""Provider adapters for the prebuilt NL-to-SQL service."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from engine.llm.catalog import schema_description

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class TextToSQLProvider(Protocol):
    def generate(self, question: str, history: list[dict[str, str]] | None = None) -> tuple[str, str, list[str]]: ...


MOCK_QUERIES = {
    "what is total net revenue by sales channel?": ("SELECT sales_channel, SUM(net_revenue) AS net_revenue FROM gold.order_360 GROUP BY sales_channel ORDER BY net_revenue DESC", "Net revenue is aggregated at the order grain by sales channel.", ["gold.order_360"]),
    "which channels had the highest refund rate?": ("SELECT sales_channel, AVG(CASE WHEN refunded_amount > 0 THEN 1.0 ELSE 0.0 END) AS refund_rate FROM gold.order_360 GROUP BY sales_channel ORDER BY refund_rate DESC", "Refund rate is the share of orders with a positive completed refund.", ["gold.order_360"]),
    "how many orders were placed each day?": ("SELECT order_date, COUNT(*) AS total_orders FROM gold.order_360 GROUP BY order_date ORDER BY order_date", "Orders are counted from the one-row-per-order Gold table.", ["gold.order_360"]),
    "what is the average order value by channel?": ("SELECT sales_channel, AVG(net_revenue) AS average_order_value FROM gold.order_360 GROUP BY sales_channel ORDER BY average_order_value DESC", "Average order value uses net revenue per resolved order.", ["gold.order_360"]),
    "which products had stockouts?": ("SELECT product_id, metric_date FROM gold.product_daily WHERE stockout_flag IS TRUE ORDER BY metric_date, product_id", "Stockouts are product-day rows with zero available inventory.", ["gold.product_daily"]),
    "which product categories generated the most revenue?": ("SELECT active_category, SUM(net_revenue) AS net_revenue FROM gold.product_daily GROUP BY active_category ORDER BY net_revenue DESC", "Product revenue is aggregated from product-day facts.", ["gold.product_daily"]),
    "how many customers were active each day?": ("SELECT metric_date, COUNT(DISTINCT customer_id) AS active_customers FROM gold.customer_daily WHERE order_count > 0 GROUP BY metric_date ORDER BY metric_date", "Active customers are customers with at least one order on the date.", ["gold.customer_daily"]),
    "what is the repeat customer rate by day?": ("SELECT metric_date, AVG(CASE WHEN repeat_customer_flag THEN 1.0 ELSE 0.0 END) AS repeat_customer_rate FROM gold.customer_daily GROUP BY metric_date ORDER BY metric_date", "Repeat rate is calculated over active customer-day rows.", ["gold.customer_daily"]),
    "which campaigns had the best roas?": ("SELECT campaign_id, SUM(net_revenue) / NULLIF(SUM(campaign_spend), 0) AS roas FROM gold.channel_campaign_daily GROUP BY campaign_id HAVING SUM(campaign_spend) > 0 ORDER BY roas DESC", "ROAS is attributed net revenue divided by campaign spend; campaigns without spend are excluded from the ranking.", ["gold.channel_campaign_daily"]),
    "which channel and campaign combination drove the most orders?": ("SELECT sales_channel, campaign_id, SUM(attributed_orders) AS orders FROM gold.channel_campaign_daily GROUP BY sales_channel, campaign_id ORDER BY orders DESC", "Orders are grouped at the channel-campaign-day grain before aggregation.", ["gold.channel_campaign_daily"]),
    "what was the daily net revenue?": ("SELECT metric_date, net_revenue FROM gold.executive_kpis_daily ORDER BY metric_date", "The executive KPI table provides the daily net revenue metric.", ["gold.executive_kpis_daily"]),
    "what was the daily refund rate?": ("SELECT metric_date, refund_rate FROM gold.executive_kpis_daily ORDER BY metric_date", "The executive KPI table provides the daily refund rate metric.", ["gold.executive_kpis_daily"]),
    "what was the daily return rate?": ("SELECT metric_date, return_rate FROM gold.executive_kpis_daily ORDER BY metric_date", "The executive KPI table provides the daily return rate metric.", ["gold.executive_kpis_daily"]),
    "what was the daily stockout rate?": ("SELECT metric_date, stockout_rate FROM gold.executive_kpis_daily ORDER BY metric_date", "The executive KPI table provides the daily stockout rate metric.", ["gold.executive_kpis_daily"]),
    "which orders were fully refunded?": ("SELECT order_id, refunded_amount, net_revenue FROM gold.order_360 WHERE refunded_amount > 0 AND net_revenue <= 0 ORDER BY order_id", "Fully refunded orders have refunds equal to or greater than their pre-refund revenue.", ["gold.order_360"]),
    "which customers generated the most net revenue?": ("SELECT customer_id, SUM(net_revenue) AS net_revenue FROM gold.customer_daily GROUP BY customer_id ORDER BY net_revenue DESC", "Customer revenue is aggregated from customer-day facts.", ["gold.customer_daily"]),
    "which customers contacted support after ordering?": ("SELECT customer_id, SUM(support_contacts) AS support_contacts FROM gold.customer_daily WHERE support_contacts > 0 GROUP BY customer_id ORDER BY support_contacts DESC", "Support contacts are linked to customer-day facts.", ["gold.customer_daily"]),
    "which categories had the highest refund amount?": ("SELECT active_category, SUM(gross_revenue - net_revenue) AS refund_amount FROM gold.product_daily GROUP BY active_category ORDER BY refund_amount DESC", "The product-day answer uses the difference between gross and net revenue as a compact teaching metric.", ["gold.product_daily"]),
    "how much campaign spend was recorded?": ("SELECT campaign_id, SUM(campaign_spend) AS campaign_spend FROM gold.channel_campaign_daily GROUP BY campaign_id ORDER BY campaign_id", "Campaign spend is summed after channel-campaign-day deduplication.", ["gold.channel_campaign_daily"]),
    "which days had the most orders?": ("SELECT metric_date, total_orders FROM gold.executive_kpis_daily ORDER BY total_orders DESC, metric_date", "Daily order volume comes from executive KPI facts.", ["gold.executive_kpis_daily"]),
    "what are the top products by units sold?": ("SELECT product_id, SUM(units_sold) AS units_sold FROM gold.product_daily GROUP BY product_id ORDER BY units_sold DESC", "Product units are summed from product-day facts.", ["gold.product_daily"]),
    "what is the captured payment total by day?": ("SELECT order_date, SUM(captured_payment_amount) AS captured_payment_amount FROM gold.order_360 GROUP BY order_date ORDER BY order_date", "Captured payment totals are deduplicated at the order grain.", ["gold.order_360"]),
    "what is the refund total by day?": ("SELECT order_date, SUM(refunded_amount) AS refunded_amount FROM gold.order_360 GROUP BY order_date ORDER BY order_date", "Refund totals are deduplicated at the order grain.", ["gold.order_360"]),
    "which channels have the most repeat customers?": ("SELECT active_channel, COUNT(DISTINCT customer_id) AS repeat_customers FROM gold.customer_daily WHERE repeat_customer_flag GROUP BY active_channel ORDER BY repeat_customers DESC", "Repeat customers are grouped by their active channel on each customer-day.", ["gold.customer_daily"]),
    "when was the data last refreshed?": ("SELECT MAX(data_freshness_utc) AS last_refresh_utc FROM gold.executive_kpis_daily", "Freshness is read from the executive KPI contract.", ["gold.executive_kpis_daily"]),
}


@dataclass(frozen=True)
class MockProvider:
    def generate(self, question: str, history: list[dict[str, str]] | None = None) -> tuple[str, str, list[str]]:
        key = " ".join(question.lower().split())
        try:
            return MOCK_QUERIES[key]
        except KeyError as exc:
            raise ValueError("Mock provider does not have a benchmark query for this question") from exc


@dataclass(frozen=True)
class OpenAICompatibleProvider:
    api_key: str
    base_url: str
    model: str

    def generate(self, question: str, history: list[dict[str, str]] | None = None) -> tuple[str, str, list[str]]:
        history_text = ""
        if history:
            history_text = "\nConversation context:\n" + "\n".join(
                f"{message.get('role', 'user')}: {message.get('content', '')[:500]}"
                for message in history[-6:]
            )
        prompt = (
            "You are a read-only analytics SQL generator. Return valid JSON with keys "
            "sql, explanation, tables_used. Use only the Gold tables. The schema catalog "
            "is authoritative: verify every table and column before returning SQL. "
            "Do not invent columns, and do not use a date column from a table that does "
            "not contain it. Prefer gold.executive_kpis_daily for daily executive metrics. "
            "For a question asking which campaigns have the best ROAS, aggregate by "
            "campaign_id and calculate SUM(net_revenue) / NULLIF(SUM(campaign_spend), 0); "
            "exclude groups with no campaign spend, and do not rank individual daily ROAS "
            "rows unless a date-level answer is requested.\n\n"
            f"Schema catalog:\n{schema_description()}\n\nQuestion: {question}{history_text}"
        )
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        result = json.loads(content)
        return str(result["sql"]), str(result.get("explanation", "")), list(result.get("tables_used", []))


def build_provider() -> TextToSQLProvider:
    provider = os.getenv("NL2SQL_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockProvider()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when NL2SQL_PROVIDER is not mock")
    return OpenAICompatibleProvider(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
