-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Santa's Delivery Dashboard - SQL Queries
-- MAGIC 
-- MAGIC This notebook contains SQL queries for creating visualizations in the Databricks SQL Dashboard.
-- MAGIC Run these queries against the Gold tables from the DLT pipeline.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 1: Overall Delivery Progress (KPI Card)

-- COMMAND ----------

-- Overall progress - Latest metrics
SELECT 
  window_start,
  period_deliveries as total_deliveries,
  period_gifts as total_gifts,
  period_successful as successful_deliveries,
  period_delayed as delayed_deliveries,
  ROUND(success_rate_percentage, 2) as success_rate_pct,
  ROUND(delay_rate_percentage, 2) as delay_rate_pct,
  ROUND(avg_time_to_delivery_minutes, 2) as avg_delivery_time_mins,
  ROUND(period_distance_km, 2) as total_distance_km,
  ROUND(avg_reindeer_speed, 2) as avg_speed_kmh,
  ROUND(avg_magic_level * 100, 2) as magic_level_pct
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 2: Delivery Completion Trend (Line Chart)

-- COMMAND ----------

-- Time series of completion percentage over time
SELECT 
  window_start,
  ROUND(completion_percentage, 2) as completion_pct,
  total_deliveries,
  successful_deliveries,
  delayed_deliveries
FROM gold_delivery_summary_realtime
ORDER BY window_start DESC
LIMIT 60  -- Last hour of 1-minute windows

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 3: Deliveries by Region (Bar Chart)

-- COMMAND ----------

-- Most recent 5-minute window by region
WITH latest_window AS (
  SELECT MAX(window_start) as max_window
  FROM gold_delivery_by_region
)
SELECT 
  r.region,
  r.total_deliveries,
  r.total_gifts,
  r.successful_deliveries,
  ROUND(r.success_rate_percentage, 2) as success_rate_pct,
  r.countries_in_region,
  r.cities_visited,
  ROUND(r.avg_delivery_time, 2) as avg_delivery_time_sec
FROM gold_delivery_by_region r
INNER JOIN latest_window lw ON r.window_start = lw.max_window
ORDER BY r.total_deliveries DESC

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 4: Performance by Gift Type (Horizontal Bar)

-- COMMAND ----------

-- Latest performance metrics by gift type
WITH latest_window AS (
  SELECT MAX(window_start) as max_window
  FROM gold_delivery_by_gift_type
)
SELECT 
  g.gift_type,
  g.total_deliveries,
  g.total_gifts,
  ROUND(g.avg_delivery_time, 2) as avg_delivery_time_sec,
  ROUND(g.avg_adjusted_delivery_time, 2) as avg_adjusted_time_sec,
  ROUND(g.success_rate_percentage, 2) as success_rate_pct
FROM gold_delivery_by_gift_type g
INNER JOIN latest_window lw ON g.window_start = lw.max_window
ORDER BY g.total_deliveries DESC

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 5: Top 10 Cities by Delivery Volume (Table/Bar Chart)

-- COMMAND ----------

-- Top cities with most deliveries in recent window
WITH latest_window AS (
  SELECT MAX(window_start) as max_window
  FROM gold_top_cities
)
SELECT 
  t.city,
  t.country,
  t.region,
  t.total_deliveries,
  t.total_gifts,
  t.successful_deliveries,
  ROUND(t.avg_delivery_time, 2) as avg_delivery_time_sec
FROM gold_top_cities t
INNER JOIN latest_window lw ON t.window_start = lw.max_window
ORDER BY t.total_deliveries DESC
LIMIT 10

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 6: Real-time Activity Stream (Live Table)

-- COMMAND ----------

-- Most recent deliveries with all details
SELECT 
  delivery_timestamp,
  city,
  country,
  region,
  gift_type,
  num_gifts,
  status,
  ROUND(delivery_time_seconds, 2) as delivery_time_sec,
  ROUND(distance_from_previous_km, 2) as distance_km,
  weather_condition,
  ROUND(reindeer_speed_kmh, 2) as speed_kmh,
  ROUND(magic_level * 100, 2) as magic_pct
FROM silver_santa_deliveries
ORDER BY delivery_timestamp DESC
LIMIT 100

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 7: Delivery Time Distribution (Histogram)

-- COMMAND ----------

-- Distribution of delivery times
SELECT 
  CASE 
    WHEN delivery_time_seconds < 30 THEN '0-30 sec'
    WHEN delivery_time_seconds < 45 THEN '30-45 sec'
    WHEN delivery_time_seconds < 60 THEN '45-60 sec'
    WHEN delivery_time_seconds < 90 THEN '60-90 sec'
    WHEN delivery_time_seconds < 120 THEN '90-120 sec'
    ELSE '120+ sec'
  END as time_bucket,
  COUNT(*) as delivery_count
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 1 HOUR
GROUP BY time_bucket
ORDER BY 
  CASE 
    WHEN time_bucket = '0-30 sec' THEN 1
    WHEN time_bucket = '30-45 sec' THEN 2
    WHEN time_bucket = '45-60 sec' THEN 3
    WHEN time_bucket = '60-90 sec' THEN 4
    WHEN time_bucket = '90-120 sec' THEN 5
    ELSE 6
  END

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 8: Weather Impact Analysis (Pie/Donut Chart)

-- COMMAND ----------

-- Distribution of deliveries by weather condition
SELECT 
  weather_condition,
  COUNT(*) as delivery_count,
  ROUND(AVG(delivery_time_seconds), 2) as avg_delivery_time,
  ROUND(SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 1 HOUR
GROUP BY weather_condition
ORDER BY delivery_count DESC

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 9: Distance Traveled Over Time (Area Chart)

-- COMMAND ----------

-- Cumulative distance traveled
SELECT 
  window_start,
  ROUND(total_distance_traveled_km, 2) as distance_km,
  total_deliveries,
  ROUND(avg_distance_km, 2) as avg_distance_per_delivery
FROM gold_delivery_summary_realtime
ORDER BY window_start ASC
LIMIT 100

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 10: Reindeer Performance Metrics (Gauge/KPI)

-- COMMAND ----------

-- Latest reindeer performance
SELECT 
  ROUND(avg_reindeer_speed_kmh, 2) as avg_speed_kmh,
  ROUND(avg_magic_level * 100, 2) as magic_level_pct,
  total_distance_traveled_km as total_distance_km,
  ROUND(total_distance_traveled_km / (avg_delivery_time_seconds / 3600), 2) as effective_speed_kmh,
  ROUND(avg_delivery_time_seconds, 2) as avg_time_per_delivery_sec
FROM gold_delivery_summary_realtime
ORDER BY window_start DESC
LIMIT 1

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 11: Success vs Delay Rate Trend (Dual-Axis Line Chart)

-- COMMAND ----------

-- Track success and delay rates over time
SELECT 
  window_start,
  ROUND(success_rate_percentage, 2) as success_rate,
  ROUND(delay_rate_percentage, 2) as delay_rate,
  total_deliveries
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 50

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 12: Geographic Heatmap Data (Map Visualization)

-- COMMAND ----------

-- Recent delivery locations for map plotting
SELECT 
  city,
  country,
  region,
  latitude,
  longitude,
  COUNT(*) as delivery_count,
  SUM(num_gifts) as total_gifts,
  ROUND(AVG(delivery_time_seconds), 2) as avg_delivery_time
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 30 MINUTES
GROUP BY city, country, region, latitude, longitude
ORDER BY delivery_count DESC

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 13: Delivery Status Breakdown (Stacked Bar)

-- COMMAND ----------

-- Current status distribution
SELECT 
  status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 15 MINUTES
GROUP BY status

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 14: Performance Summary Dashboard View

-- COMMAND ----------

-- Comprehensive summary for main dashboard
SELECT 
  'Overall Performance' as metric_category,
  CAST(period_deliveries as STRING) as deliveries,
  CONCAT(ROUND(success_rate_percentage, 1), '%') as success_rate,
  CONCAT(ROUND(avg_time_to_delivery_minutes, 1), ' min') as avg_time,
  CONCAT(ROUND(period_distance_km, 0), ' km') as distance,
  CONCAT(ROUND(avg_reindeer_speed, 0), ' km/h') as speed
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

