-- Useful validation and dashboard queries.

SELECT * FROM gold.executive_kpis_daily ORDER BY metric_date;

SELECT sales_channel, SUM(net_revenue) AS net_revenue,
       AVG(CASE WHEN refunded_amount > 0 THEN 1.0 ELSE 0.0 END) AS refund_rate
FROM gold.order_360
GROUP BY sales_channel
ORDER BY net_revenue DESC;

SELECT campaign_id, SUM(campaign_spend) AS spend,
       SUM(net_revenue) AS net_revenue,
       SUM(net_revenue) / NULLIF(SUM(campaign_spend), 0) AS roas
FROM gold.channel_campaign_daily
GROUP BY campaign_id
ORDER BY roas DESC NULLS LAST;

SELECT metric_date, AVG(stockout_flag::INT)::NUMERIC(14, 4) AS stockout_rate
FROM gold.product_daily
WHERE stockout_flag IS NOT NULL
GROUP BY metric_date
ORDER BY metric_date;
