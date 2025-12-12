# Quick Start Guide - Santa's Delivery Pipeline

**Unity Catalog Location**: `tleider.holiday`

## 🎯 Get Running in 5 Minutes

### Step 1: Start Data Generation (2 minutes)
1. Open `data_generator.py` in Databricks
2. Run all cells (Cmd/Ctrl + Shift + Enter)
3. Watch events generate - you'll see: "Batch X: Generated Y total delivery events"
4. Leave it running in the background

### Step 2: Create DLT Pipeline (2 minutes)
1. Go to **Workflows** → **Delta Live Tables** → **Create Pipeline**
2. Fill in:
   - **Name**: `santa_delivery_pipeline`
   - **Notebook**: Select `santa_delivery_dlt_pipeline.py`
   - **Catalog**: `tleider`
   - **Target**: `holiday`
   - **Storage**: `/Users/your_username/santa_pipeline`
   - **Configuration**: Add key `source_path` = `/tmp/santa_deliveries`
   - **Mode**: Continuous
   - **Cluster**: 2 workers, enable Photon
3. Click **Create** then **Start**

### Step 3: Verify Setup (1 minute)
1. Open `setup_verification.py`
2. Run the health check cells
3. Confirm all layers show ✓ with record counts

### Step 4: Create Dashboard
1. Open `dashboard_queries.sql`
2. Create new dashboard in SQL workspace
3. Add queries as visualizations:
   - Query 1 → Counter cards (KPIs)
   - Query 2 → Line chart (trends)
   - Query 3 → Bar chart (regions)
   - Query 6 → Table (live stream)
4. Set auto-refresh: 10 seconds

## 🎊 You're Done!

Watch Santa make deliveries in real-time!

## 📊 What You'll See

- **Success Rate**: 80-85% (most kids are on the nice list! 🎁)
- **Deliveries**: ~600/minute with default settings
- **Distance**: ~500km between cities on average
- **Speed**: 800-1200 km/h (magic sleigh! ✨)

## ⚙️ Adjust Data Volume

In `data_generator.py`, change these widgets:
```python
events_per_batch = 50      # Increase for more data
batch_interval_seconds = 5 # Decrease for faster generation
```

## 🔍 Monitor Pipeline

- **DLT UI**: Shows pipeline graph and data flow
- **Data Quality**: View expectations and dropped records
- **Lineage**: See Bronze → Silver → Gold transformations

## 🎁 Next Steps

- Customize cities in `WORLD_LOCATIONS`
- Add more gift types
- Create custom aggregations
- Build ML models for delivery predictions
- Add anomaly detection

Enjoy! 🎄

