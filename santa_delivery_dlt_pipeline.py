# Databricks notebook source
# MAGIC %md
# MAGIC # Santa's Delivery Pipeline - Delta Live Tables
# MAGIC 
# MAGIC This dp pipeline processes Santa's gift delivery data through Bronze, Silver, and Gold layers.
# MAGIC 
# MAGIC **Architecture:**
# MAGIC - Bronze: Raw ingestion from streaming source
# MAGIC - Silver: Cleaned and enriched data with proper types
# MAGIC - Gold: Aggregated metrics for real-time dashboard

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime

# COMMAND ----------

# Configuration - these will be passed in via pipeline settings
source_path = spark.conf.get("source_path", "/tmp/santa_deliveries")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer - Raw Ingestion

# COMMAND ----------

@dp.table(
    name="bronze_santa_deliveries",
    comment="Raw delivery events from Santa's sleigh tracking system",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "timestamp"
    }
)
def bronze_santa_deliveries():
    """
    Bronze table: Ingest raw streaming data from Santa's delivery system.
    This table captures all raw events without transformation.
    """
    return (
        spark.readStream
            .format("delta")
            .load(source_path)
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("ingestion_date", current_date())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer - Cleaned and Enriched

# COMMAND ----------

@dp.table(
    name="silver_santa_deliveries",
    comment="Cleaned and enriched delivery events with data quality checks",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "delivery_timestamp,region"
    }
)
@dp.expect_or_drop("valid_delivery_id", "delivery_id IS NOT NULL")
@dp.expect_or_drop("valid_timestamp", "timestamp IS NOT NULL")
@dp.expect_or_drop("valid_status", "status IN ('en_route', 'delivered', 'delayed')")
@dp.expect_or_drop("valid_coordinates", "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180")
@dp.expect_or_drop("positive_gifts", "num_gifts > 0")
def silver_santa_deliveries():
    """
    Silver table: Clean, validate, and enrich delivery data.
    - Convert timestamp strings to proper timestamp types
    - Add calculated fields
    - Apply data quality expectations
    - Add delivery performance indicators
    """
    return (
        dp.read_stream("bronze_santa_deliveries")
            .withColumn("delivery_timestamp", to_timestamp("timestamp"))
            .withColumn("delivery_date", to_date("delivery_timestamp"))
            .withColumn("delivery_hour", hour("delivery_timestamp"))
            .withColumn("delivery_minute", minute("delivery_timestamp"))
            
            # Performance indicators
            .withColumn("is_delivered", when(col("status") == "delivered", 1).otherwise(0))
            .withColumn("is_delayed", when(col("status") == "delayed", 1).otherwise(0))
            .withColumn("is_en_route", when(col("status") == "en_route", 1).otherwise(0))
            
            # Speed calculations
            .withColumn("effective_speed_kmh", 
                when(col("distance_from_previous_km") > 0,
                    (col("distance_from_previous_km") / col("delivery_time_seconds")) * 3600
                ).otherwise(0))
            
            # Weather impact
            .withColumn("weather_impact_factor",
                when(col("weather_condition") == "Clear", 1.0)
                .when(col("weather_condition") == "Cloudy", 0.95)
                .when(col("weather_condition") == "Foggy", 0.85)
                .when(col("weather_condition") == "Snowy", 0.75)
                .otherwise(1.0))
            
            # Adjusted delivery time accounting for weather
            .withColumn("adjusted_delivery_time_seconds",
                col("delivery_time_seconds") / col("weather_impact_factor"))
            
            .select(
                "delivery_id",
                "delivery_timestamp",
                "delivery_date",
                "delivery_hour",
                "delivery_minute",
                "city",
                "country",
                "region",
                "latitude",
                "longitude",
                "timezone",
                "gift_type",
                "num_gifts",
                "status",
                "delivery_time_seconds",
                "adjusted_delivery_time_seconds",
                "distance_from_previous_km",
                "weather_condition",
                "weather_impact_factor",
                "reindeer_speed_kmh",
                "magic_level",
                "is_delivered",
                "is_delayed",
                "is_en_route",
                "effective_speed_kmh",
                "ingestion_timestamp"
            )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer - Aggregated Metrics for Dashboard

# COMMAND ----------

@dp.table(
    name="gold_delivery_summary_realtime",
    comment="Real-time delivery metrics for dashboard - 1 minute windows",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.zOrderCols": "window_start"
    }
)
def gold_delivery_summary_realtime():
    """
    Gold table: Real-time aggregated metrics with 1-minute tumbling windows.
    Provides KPIs for the real-time dashboard.
    """
    return (
        dp.read_stream("silver_santa_deliveries")
            .withWatermark("delivery_timestamp", "5 minutes")
            .groupBy(
                window("delivery_timestamp", "1 minute").alias("time_window")
            )
            .agg(
                count("*").alias("total_deliveries"),
                sum("num_gifts").alias("total_gifts_delivered"),
                sum("is_delivered").alias("successful_deliveries"),
                sum("is_delayed").alias("delayed_deliveries"),
                sum("is_en_route").alias("en_route_deliveries"),
                avg("delivery_time_seconds").alias("avg_delivery_time_seconds"),
                avg("adjusted_delivery_time_seconds").alias("avg_adjusted_delivery_time_seconds"),
                avg("distance_from_previous_km").alias("avg_distance_km"),
                avg("reindeer_speed_kmh").alias("avg_reindeer_speed_kmh"),
                avg("magic_level").alias("avg_magic_level"),
                max("delivery_time_seconds").alias("max_delivery_time_seconds"),
                min("delivery_time_seconds").alias("min_delivery_time_seconds"),
                sum("distance_from_previous_km").alias("total_distance_traveled_km"),
                countDistinct("region").alias("unique_regions_visited"),
                countDistinct("country").alias("unique_countries_visited"),
                countDistinct("city").alias("unique_cities_visited")
            )
            .select(
                col("time_window.start").alias("window_start"),
                col("time_window.end").alias("window_end"),
                col("total_deliveries"),
                col("total_gifts_delivered"),
                col("successful_deliveries"),
                col("delayed_deliveries"),
                col("en_route_deliveries"),
                
                # Calculate completion percentage
                (col("successful_deliveries") / col("total_deliveries") * 100).alias("completion_percentage"),
                
                # Calculate delay rate
                (col("delayed_deliveries") / col("total_deliveries") * 100).alias("delay_rate_percentage"),
                
                col("avg_delivery_time_seconds"),
                col("avg_adjusted_delivery_time_seconds"),
                col("avg_distance_km"),
                col("avg_reindeer_speed_kmh"),
                col("avg_magic_level"),
                col("max_delivery_time_seconds"),
                col("min_delivery_time_seconds"),
                col("total_distance_traveled_km"),
                col("unique_regions_visited"),
                col("unique_countries_visited"),
                col("unique_cities_visited"),
                current_timestamp().alias("calculated_at")
            )
    )

# COMMAND ----------

@dp.table(
    name="gold_delivery_by_region",
    comment="Delivery metrics aggregated by region",
    table_properties={
        "quality": "gold"
    }
)
def gold_delivery_by_region():
    """
    Gold table: Aggregated metrics by geographic region.
    Shows performance across different world regions.
    """
    return (
        dp.read_stream("silver_santa_deliveries")
            .withWatermark("delivery_timestamp", "5 minutes")
            .groupBy(
                window("delivery_timestamp", "5 minutes").alias("time_window"),
                "region"
            )
            .agg(
                count("*").alias("total_deliveries"),
                sum("num_gifts").alias("total_gifts"),
                sum("is_delivered").alias("successful_deliveries"),
                sum("is_delayed").alias("delayed_deliveries"),
                avg("delivery_time_seconds").alias("avg_delivery_time"),
                avg("magic_level").alias("avg_magic_level"),
                sum("distance_from_previous_km").alias("total_distance_km"),
                countDistinct("country").alias("countries_in_region"),
                countDistinct("city").alias("cities_visited")
            )
            .select(
                col("time_window.start").alias("window_start"),
                col("time_window.end").alias("window_end"),
                col("region"),
                col("total_deliveries"),
                col("total_gifts"),
                col("successful_deliveries"),
                col("delayed_deliveries"),
                (col("successful_deliveries") / col("total_deliveries") * 100).alias("success_rate_percentage"),
                col("avg_delivery_time"),
                col("avg_magic_level"),
                col("total_distance_km"),
                col("countries_in_region"),
                col("cities_visited"),
                current_timestamp().alias("calculated_at")
            )
    )

# COMMAND ----------

@dp.table(
    name="gold_delivery_by_gift_type",
    comment="Delivery metrics aggregated by gift type",
    table_properties={
        "quality": "gold"
    }
)
def gold_delivery_by_gift_type():
    """
    Gold table: Performance metrics by gift type.
    Helps understand which types of gifts take longer to deliver.
    """
    return (
        dp.read_stream("silver_santa_deliveries")
            .withWatermark("delivery_timestamp", "5 minutes")
            .groupBy(
                window("delivery_timestamp", "5 minutes").alias("time_window"),
                "gift_type"
            )
            .agg(
                count("*").alias("total_deliveries"),
                sum("num_gifts").alias("total_gifts"),
                sum("is_delivered").alias("successful_deliveries"),
                avg("delivery_time_seconds").alias("avg_delivery_time"),
                avg("adjusted_delivery_time_seconds").alias("avg_adjusted_delivery_time"),
                max("delivery_time_seconds").alias("max_delivery_time"),
                min("delivery_time_seconds").alias("min_delivery_time")
            )
            .select(
                col("time_window.start").alias("window_start"),
                col("time_window.end").alias("window_end"),
                col("gift_type"),
                col("total_deliveries"),
                col("total_gifts"),
                col("successful_deliveries"),
                (col("successful_deliveries") / col("total_deliveries") * 100).alias("success_rate_percentage"),
                col("avg_delivery_time"),
                col("avg_adjusted_delivery_time"),
                col("max_delivery_time"),
                col("min_delivery_time"),
                current_timestamp().alias("calculated_at")
            )
    )

# COMMAND ----------

@dp.table(
    name="gold_overall_progress",
    comment="Overall delivery progress and cumulative statistics",
    table_properties={
        "quality": "gold"
    }
)
def gold_overall_progress():
    """
    Gold table: Cumulative delivery statistics.
    Tracks overall progress throughout Santa's journey.
    """
    return (
        dp.read_stream("silver_santa_deliveries")
            .withWatermark("delivery_timestamp", "5 minutes")
            .groupBy(
                window("delivery_timestamp", "10 minutes").alias("time_window")
            )
            .agg(
                count("*").alias("period_deliveries"),
                sum("num_gifts").alias("period_gifts"),
                sum("is_delivered").alias("period_successful"),
                sum("is_delayed").alias("period_delayed"),
                sum("is_en_route").alias("period_en_route"),
                avg("delivery_time_seconds").alias("avg_time_to_delivery"),
                sum("distance_from_previous_km").alias("period_distance_km"),
                avg("reindeer_speed_kmh").alias("avg_reindeer_speed"),
                avg("magic_level").alias("avg_magic_level"),
                
                # Weather impact
                sum(when(col("weather_condition") == "Clear", 1).otherwise(0)).alias("clear_weather_count"),
                sum(when(col("weather_condition") == "Snowy", 1).otherwise(0)).alias("snowy_weather_count"),
                sum(when(col("weather_condition") == "Foggy", 1).otherwise(0)).alias("foggy_weather_count"),
                sum(when(col("weather_condition") == "Cloudy", 1).otherwise(0)).alias("cloudy_weather_count")
            )
            .select(
                col("time_window.start").alias("window_start"),
                col("time_window.end").alias("window_end"),
                col("period_deliveries"),
                col("period_gifts"),
                col("period_successful"),
                col("period_delayed"),
                col("period_en_route"),
                (col("period_successful") / col("period_deliveries") * 100).alias("success_rate_percentage"),
                (col("period_delayed") / col("period_deliveries") * 100).alias("delay_rate_percentage"),
                col("avg_time_to_delivery"),
                (col("avg_time_to_delivery") / 60).alias("avg_time_to_delivery_minutes"),
                col("period_distance_km"),
                col("avg_reindeer_speed"),
                col("avg_magic_level"),
                col("clear_weather_count"),
                col("snowy_weather_count"),
                col("foggy_weather_count"),
                col("cloudy_weather_count"),
                current_timestamp().alias("calculated_at")
            )
    )

# COMMAND ----------

@dp.table(
    name="gold_top_cities",
    comment="Top cities by delivery volume",
    table_properties={
        "quality": "gold"
    }
)
def gold_top_cities():
    """
    Gold table: Rank cities by delivery volume and gifts delivered.
    """
    return (
        dp.read_stream("silver_santa_deliveries")
            .withWatermark("delivery_timestamp", "5 minutes")
            .groupBy(
                window("delivery_timestamp", "15 minutes").alias("time_window"),
                "city",
                "country",
                "region"
            )
            .agg(
                count("*").alias("total_deliveries"),
                sum("num_gifts").alias("total_gifts"),
                sum("is_delivered").alias("successful_deliveries"),
                avg("delivery_time_seconds").alias("avg_delivery_time")
            )
            .select(
                col("time_window.start").alias("window_start"),
                col("time_window.end").alias("window_end"),
                col("city"),
                col("country"),
                col("region"),
                col("total_deliveries"),
                col("total_gifts"),
                col("successful_deliveries"),
                col("avg_delivery_time"),
                current_timestamp().alias("calculated_at")
            )
    )

