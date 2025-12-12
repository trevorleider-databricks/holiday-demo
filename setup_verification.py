# Databricks notebook source
# MAGIC %md
# MAGIC # Setup and Verification Notebook
# MAGIC 
# MAGIC Use this notebook to verify your pipeline setup and check data flow.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Check Data Generator Output

# COMMAND ----------

# DBTITLE 1,Verify Source Data Exists
source_path = "/tmp/santa_deliveries"

# Check if data exists
try:
    df = spark.read.format("delta").load(source_path)
    count = df.count()
    print(f"✓ Source data found: {count} records")
    print(f"✓ Path: {source_path}")
    display(df.limit(10))
except Exception as e:
    print(f"✗ Error reading source data: {e}")
    print(f"  Make sure data_generator.py is running!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Check DLT Pipeline Tables

# COMMAND ----------

# DBTITLE 1,List Pipeline Tables
database = "santa_delivery_db"

# Show all tables in the target database
tables = spark.sql(f"SHOW TABLES IN {database}").collect()

print(f"Tables in {database}:")
print("-" * 60)
for table in tables:
    table_name = table.tableName
    try:
        count = spark.sql(f"SELECT COUNT(*) as cnt FROM {database}.{table_name}").collect()[0].cnt
        print(f"  ✓ {table_name}: {count} records")
    except Exception as e:
        print(f"  ✗ {table_name}: Error - {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Verify Bronze Layer

# COMMAND ----------

# DBTITLE 1,Bronze Layer Sample
try:
    bronze = spark.table(f"{database}.bronze_santa_deliveries")
    print(f"Bronze records: {bronze.count()}")
    display(bronze.orderBy("ingestion_timestamp", ascending=False).limit(20))
except Exception as e:
    print(f"Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Verify Silver Layer

# COMMAND ----------

# DBTITLE 1,Silver Layer Sample
try:
    silver = spark.table(f"{database}.silver_santa_deliveries")
    print(f"Silver records: {silver.count()}")
    
    # Show data quality stats
    print("\nData Quality Summary:")
    silver.groupBy("status").count().show()
    
    display(silver.orderBy("delivery_timestamp", ascending=False).limit(20))
except Exception as e:
    print(f"Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Verify Gold Layer Aggregations

# COMMAND ----------

# DBTITLE 1,Gold - Real-time Summary
try:
    gold_summary = spark.table(f"{database}.gold_delivery_summary_realtime")
    print(f"Gold summary records: {gold_summary.count()}")
    display(gold_summary.orderBy("window_start", ascending=False).limit(10))
except Exception as e:
    print(f"Error: {e}")

# COMMAND ----------

# DBTITLE 1,Gold - Regional Performance
try:
    gold_region = spark.table(f"{database}.gold_delivery_by_region")
    display(gold_region.orderBy("window_start", ascending=False).limit(20))
except Exception as e:
    print(f"Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Data Flow Verification

# COMMAND ----------

# DBTITLE 1,End-to-End Data Flow Check
from datetime import datetime

print("=" * 70)
print("SANTA'S DELIVERY PIPELINE - HEALTH CHECK")
print("=" * 70)
print(f"Check Time: {datetime.now()}")
print()

# Check each layer
layers = [
    ("Source", source_path, "delta"),
    ("Bronze", f"{database}.bronze_santa_deliveries", "table"),
    ("Silver", f"{database}.silver_santa_deliveries", "table"),
    ("Gold - Summary", f"{database}.gold_delivery_summary_realtime", "table"),
    ("Gold - Region", f"{database}.gold_delivery_by_region", "table"),
    ("Gold - Gift Type", f"{database}.gold_delivery_by_gift_type", "table"),
    ("Gold - Progress", f"{database}.gold_overall_progress", "table"),
    ("Gold - Cities", f"{database}.gold_top_cities", "table")
]

for layer_name, path, read_type in layers:
    try:
        if read_type == "delta":
            count = spark.read.format("delta").load(path).count()
        else:
            count = spark.table(path).count()
        
        status = "✓" if count > 0 else "⚠"
        print(f"{status} {layer_name:20s}: {count:,} records")
    except Exception as e:
        print(f"✗ {layer_name:20s}: ERROR - {str(e)[:50]}")

print()
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Quick Performance Stats

# COMMAND ----------

# DBTITLE 1,Overall Statistics
try:
    stats = spark.sql(f"""
        SELECT 
            COUNT(*) as total_deliveries,
            SUM(num_gifts) as total_gifts,
            ROUND(AVG(delivery_time_seconds), 2) as avg_delivery_time,
            ROUND(SUM(distance_from_previous_km), 2) as total_distance,
            COUNT(DISTINCT region) as regions_visited,
            COUNT(DISTINCT country) as countries_visited,
            COUNT(DISTINCT city) as cities_visited,
            ROUND(SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct
        FROM {database}.silver_santa_deliveries
    """)
    
    display(stats)
except Exception as e:
    print(f"Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Real-time Data Rate

# COMMAND ----------

# DBTITLE 1,Data Ingestion Rate (Last 5 Minutes)
try:
    rate = spark.sql(f"""
        SELECT 
            DATE_FORMAT(delivery_timestamp, 'yyyy-MM-dd HH:mm') as minute,
            COUNT(*) as events_per_minute,
            SUM(num_gifts) as gifts_per_minute
        FROM {database}.silver_santa_deliveries
        WHERE delivery_timestamp >= current_timestamp() - INTERVAL 5 MINUTES
        GROUP BY DATE_FORMAT(delivery_timestamp, 'yyyy-MM-dd HH:mm')
        ORDER BY minute DESC
    """)
    
    display(rate)
except Exception as e:
    print(f"Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Troubleshooting Tips
# MAGIC 
# MAGIC ### If no data in source:
# MAGIC 1. Ensure `data_generator.py` is running
# MAGIC 2. Check the output path matches
# MAGIC 3. Verify write permissions to `/tmp/santa_deliveries`
# MAGIC 
# MAGIC ### If Bronze is empty:
# MAGIC 1. Check DLT pipeline is running (Continuous mode)
# MAGIC 2. Verify `source_path` configuration in pipeline
# MAGIC 3. Look for errors in DLT pipeline logs
# MAGIC 
# MAGIC ### If Silver is empty but Bronze has data:
# MAGIC 1. Check data quality expectations (might be dropping bad records)
# MAGIC 2. Review DLT pipeline logs for validation errors
# MAGIC 
# MAGIC ### If Gold is empty but Silver has data:
# MAGIC 1. Wait 1-2 minutes for first aggregation window
# MAGIC 2. Check for streaming query errors in pipeline logs
# MAGIC 3. Verify watermark settings aren't too aggressive

