# Troubleshooting Guide

## 🔍 Common Issues and Solutions

### Issue 1: Data Generator Not Creating Data

**Symptoms:**
- `data_generator.py` runs but no output
- Error: "Cannot write to path"
- Cell completes but shows 0 batches

**Solutions:**

✅ **Check Permissions:**
```python
# Test write access
test_path = "/tmp/test_write"
spark.range(1).write.mode("overwrite").parquet(test_path)
print("✓ Write permission OK")
```

✅ **Verify Path:**
```python
# Check if path exists and has data
dbutils.fs.ls("/tmp/santa_deliveries")
```

✅ **Check for Errors:**
- Look at cell output for stack traces
- Check cluster logs: Cluster UI → Event Log

✅ **Restart Clean:**
```python
# Clear and restart
dbutils.fs.rm("/tmp/santa_deliveries", recurse=True)
dbutils.fs.rm("/tmp/santa_deliveries_checkpoint", recurse=True)
# Then run data_generator.py again
```

---

### Issue 2: DLT Pipeline Won't Start

**Symptoms:**
- Pipeline status: "Failed to start"
- Error: "Invalid configuration"
- Pipeline graph doesn't render

**Solutions:**

✅ **Verify Configuration:**
```json
{
  "configuration": {
    "source_path": "/tmp/santa_deliveries"  // Must exist and have data
  }
}
```

✅ **Check Notebook Path:**
- Ensure `santa_delivery_dlt_pipeline.py` is uploaded
- Path must be absolute: `/Users/your.name/santa_delivery_dlt_pipeline`
- Not relative: `santa_delivery_dlt_pipeline`

✅ **Validate Target Database:**
- Database name must be valid SQL identifier
- No spaces or special characters
- Use: `santa_delivery_db` not `Santa's Delivery DB`

✅ **Check Cluster Configuration:**
- Minimum: 2 workers
- Runtime: 13.3 LTS or higher
- Photon: Recommended but not required
- Mode: Continuous (not Triggered)

---

### Issue 3: Bronze Table Empty

**Symptoms:**
- Pipeline running but bronze table has 0 records
- Silver/Gold tables also empty
- No errors in pipeline logs

**Solutions:**

✅ **Verify Source Data:**
```python
# Check source has data
df = spark.read.format("delta").load("/tmp/santa_deliveries")
print(f"Source records: {df.count()}")
```

✅ **Check Path Configuration:**
```python
# In pipeline config, must match generator output
source_path = "/tmp/santa_deliveries"  # Exact match required
```

✅ **Restart Pipeline:**
1. Stop the pipeline
2. Wait 30 seconds
3. Start again
4. Wait 2-3 minutes for first data

✅ **Check for Permissions:**
- Pipeline cluster must have read access to source path
- Check cluster IAM role (if using cloud storage)

---

### Issue 4: Silver Table Empty (Bronze Has Data)

**Symptoms:**
- Bronze table has records
- Silver table has 0 records
- Expectation metrics show "dropped records"

**Solutions:**

✅ **Check Data Quality Metrics:**
```sql
-- In DLT UI, check "Data Quality" tab
-- Look for expectations with high drop rates
```

✅ **Review Expectations:**
The pipeline has these expectations:
- `valid_delivery_id`: delivery_id IS NOT NULL
- `valid_timestamp`: timestamp IS NOT NULL
- `valid_status`: status IN ('en_route', 'delivered', 'delayed')
- `valid_coordinates`: lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180
- `positive_gifts`: num_gifts > 0

✅ **Temporarily Relax Expectations:**
```python
# In santa_delivery_dlt_pipeline.py, change to warnings:
@dlt.expect("valid_status", "status IN ('en_route', 'delivered', 'delayed')")
# Instead of:
@dlt.expect_or_drop("valid_status", ...)
```

✅ **Check Source Data Quality:**
```python
# Verify source data format
df = spark.read.format("delta").load("/tmp/santa_deliveries")
df.filter("delivery_id IS NULL").count()  # Should be 0
df.filter("status NOT IN ('en_route', 'delivered', 'delayed')").count()  # Should be 0
```

---

### Issue 5: Gold Tables Empty (Silver Has Data)

**Symptoms:**
- Silver table has records
- Gold aggregation tables are empty
- No errors visible

**Solutions:**

✅ **Wait for Aggregation Window:**
- First aggregation requires a complete window
- 1-minute windows: wait 90 seconds
- 5-minute windows: wait 6-7 minutes

✅ **Check Watermark:**
```python
# Watermark is 5 minutes - data must be within this threshold
# Very old data might be dropped
```

✅ **Verify Streaming Query Status:**
```sql
-- Check if streaming queries are running
SHOW STREAMS
```

✅ **Look for Processing Errors:**
- DLT UI → Specific gold table → View logs
- Search for "watermark" or "aggregation" errors

---

### Issue 6: Dashboard Shows No Data

**Symptoms:**
- Queries return 0 rows
- Error: "Table not found"
- Charts are empty

**Solutions:**

✅ **Verify Table Names:**
```sql
-- Check what tables exist
SHOW TABLES IN santa_delivery_db;
```

✅ **Check Database Context:**
```sql
-- Ensure queries reference correct database
USE santa_delivery_db;

-- Or use fully qualified names
SELECT * FROM santa_delivery_db.gold_delivery_summary_realtime;
```

✅ **Verify Data Freshness:**
```sql
-- Check latest data timestamp
SELECT 
  MAX(window_start) as latest_window,
  COUNT(*) as record_count
FROM gold_delivery_summary_realtime;
```

✅ **Check Query Permissions:**
- SQL warehouse must have access to tables
- User must have SELECT permissions on database

---

### Issue 7: Dashboard Updates Slowly

**Symptoms:**
- Dashboard shows stale data
- Refresh takes >1 minute
- "Running query..." persists

**Solutions:**

✅ **Optimize Query:**
```sql
-- Add LIMIT to large tables
SELECT * FROM silver_santa_deliveries
ORDER BY delivery_timestamp DESC
LIMIT 1000  -- Instead of scanning entire table
```

✅ **Use Latest Window Pattern:**
```sql
-- More efficient than ORDER BY + LIMIT
WITH latest AS (
  SELECT MAX(window_start) as max_window
  FROM gold_delivery_summary_realtime
)
SELECT g.* 
FROM gold_delivery_summary_realtime g
INNER JOIN latest l ON g.window_start = l.max_window;
```

✅ **Check SQL Warehouse:**
- Size: Small might be underpowered
- Try Medium or Large warehouse
- Enable auto-scaling
- Check queue: Workspace Settings → SQL Warehouses

✅ **Adjust Refresh Rate:**
- Don't set <10 seconds
- Consider 30-60 seconds for large dashboards
- Reduce concurrent widget refreshes

---

### Issue 8: High Latency in Pipeline

**Symptoms:**
- Long delay from generation → dashboard
- Processing lag increasing
- Cluster at max capacity

**Solutions:**

✅ **Scale Cluster:**
```json
{
  "clusters": [{
    "num_workers": 4,  // Increase from 2
    "autoscale": {
      "min_workers": 2,
      "max_workers": 8
    }
  }]
}
```

✅ **Enable Photon:**
- Significant speedup for SQL operations
- Especially helpful for aggregations
- Configure in pipeline settings

✅ **Optimize Aggregation Windows:**
```python
# Reduce window count if too many
# Combine multiple small windows
.groupBy(window("delivery_timestamp", "5 minutes"))  # Instead of 1 minute
```

✅ **Check Data Volume:**
```python
# Reduce generation rate if testing
events_per_batch = 25  # Down from 50
batch_interval_seconds = 10  # Up from 5
```

---

### Issue 9: Unexpected Data Values

**Symptoms:**
- Success rate is 0% or 100%
- Deliveries in wrong cities
- Negative distances

**Solutions:**

✅ **Check Data Generation Logic:**
```python
# Review weighted random choices
STATUS_WEIGHTS = [0.15, 0.80, 0.05]  # en_route, delivered, delayed
```

✅ **Verify Calculations:**
```sql
-- Debug specific calculations
SELECT 
  delivery_id,
  status,
  is_delivered,
  is_delayed,
  successful_deliveries,
  total_deliveries,
  completion_percentage
FROM gold_delivery_summary_realtime
WHERE completion_percentage NOT BETWEEN 0 AND 100;
```

✅ **Check for Division by Zero:**
```python
# In pipeline, ensure denominator checks
(col("successful_deliveries") / col("total_deliveries") * 100)
# Should be:
when(col("total_deliveries") > 0,
  col("successful_deliveries") / col("total_deliveries") * 100
).otherwise(0)
```

---

### Issue 10: Pipeline Keeps Failing

**Symptoms:**
- Pipeline status: "Failed"
- Automatic retries happening
- Error in event log

**Solutions:**

✅ **Check Recent Errors:**
```
DLT UI → Pipeline → Event Log → Filter: "ERROR"
```

✅ **Common Error Messages:**

**"Stream-stream join not supported"**
```python
# Don't join two streaming DFs
# Materialize one side first
```

**"Watermark required"**
```python
# Add watermark to all streaming aggregations
.withWatermark("delivery_timestamp", "5 minutes")
```

**"Output mode not supported"**
```python
# Use complete mode for some aggregations
# Not required for append-only streams
```

✅ **Reset Pipeline State:**
1. Stop pipeline
2. Delete pipeline storage:
   ```python
   dbutils.fs.rm("/Users/username/santa_delivery_pipeline", recurse=True)
   ```
3. Restart pipeline (clean slate)

✅ **Check Spark Configuration:**
```json
{
  "spark_conf": {
    "spark.databricks.delta.preview.enabled": "true",
    "spark.sql.adaptive.enabled": "true"
  }
}
```

---

## 🔧 Debugging Tools

### Tool 1: Pipeline Event Log
```
DLT UI → Your Pipeline → Event Log
- Filter by ERROR, WARN
- Look for exception stack traces
- Check timing (slow stages)
```

### Tool 2: Data Quality Dashboard
```
DLT UI → Your Pipeline → Data Quality Tab
- See expectation pass rates
- Identify data issues
- Track dropped records
```

### Tool 3: Lineage View
```
DLT UI → Your Pipeline → Lineage
- Visualize data flow
- Identify bottlenecks
- Verify dependencies
```

### Tool 4: Manual Query Testing
```sql
-- Test transformations directly
SELECT 
  *,
  to_timestamp(timestamp) as delivery_timestamp,
  CASE WHEN status = 'delivered' THEN 1 ELSE 0 END as is_delivered
FROM delta.`/tmp/santa_deliveries`
LIMIT 100;
```

### Tool 5: Streaming Query Monitoring
```python
# In a separate notebook
for stream in spark.streams.active:
    print(f"Stream: {stream.name}")
    print(f"Status: {stream.status}")
    print(f"Recent Progress: {stream.recentProgress}")
```

---

## 📞 Still Stuck?

### Step 1: Run Verification Notebook
```python
# Run setup_verification.py
# Check all health checks pass
```

### Step 2: Check System Requirements
- Databricks Runtime: 13.3 LTS or higher
- DLT: Available in your workspace
- Permissions: Can create tables and clusters
- Storage: At least 10 GB available

### Step 3: Review Logs Systematically
1. Data Generator output
2. DLT Pipeline event log
3. Cluster event log
4. SQL warehouse query history

### Step 4: Start Fresh
```python
# Nuclear option - clean everything
dbutils.fs.rm("/tmp/santa_deliveries", recurse=True)
dbutils.fs.rm("/tmp/santa_deliveries_checkpoint", recurse=True)
spark.sql("DROP DATABASE IF EXISTS santa_delivery_db CASCADE")

# Then follow QUICKSTART.md from step 1
```

---

## 💡 Pro Tips

1. **Always check data at the source first** - if generation is broken, pipeline will be empty
2. **Wait for full window cycles** - aggregations need complete windows
3. **Use verification notebook** - automates many checks
4. **Monitor resource usage** - scale cluster if needed
5. **Check permissions** - many issues are access-related
6. **Read error messages carefully** - Spark errors are verbose but informative
7. **Test queries in SQL editor** - before adding to dashboard
8. **Use LIMIT in development** - speeds up iteration
9. **Enable auto-scaling** - handles variable loads
10. **Keep it simple** - start with small windows and scale up

---

## 📊 Health Check Checklist

Run through this before troubleshooting:

- [ ] Data generator is running (not stopped)
- [ ] Source path has data (>0 records)
- [ ] DLT pipeline status is "Running"
- [ ] Bronze table has records
- [ ] Silver table has records (check after 1 min)
- [ ] Gold tables have records (check after window duration)
- [ ] Database exists: `santa_delivery_db`
- [ ] SQL warehouse is running
- [ ] Dashboard queries use correct database name
- [ ] Auto-refresh is enabled on dashboard
- [ ] At least 5 minutes have passed since starting

If all ✓ but still issues, review specific error messages above.

