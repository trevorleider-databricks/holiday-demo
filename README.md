# Santa's Gift Delivery Streaming Pipeline

A Databricks Delta Live Tables (DLT) streaming pipeline that simulates Santa's gift deliveries around the world with real-time analytics and dashboards.

## 🎄 Project Overview

This project demonstrates a complete streaming data pipeline using Databricks and Spark Structured Streaming with declarative DLT logic. It simulates Santa's sleigh making gift deliveries to 30+ cities worldwide, tracking performance metrics, weather conditions, and delivery success rates in real-time.

## 🏗️ Architecture

### Pipeline Layers (Medallion Architecture)

1. **Bronze Layer** (`bronze_santa_deliveries`)
   - Raw event ingestion from streaming source
   - Preserves original data with ingestion timestamps
   - No transformations or quality checks

2. **Silver Layer** (`silver_santa_deliveries`)
   - Cleaned and validated data
   - Data quality expectations enforced
   - Enriched with calculated fields (performance indicators, speed calculations, weather impact)
   - Type conversions and proper timestamp handling

3. **Gold Layer** (Multiple aggregated tables)
   - `gold_delivery_summary_realtime`: 1-minute window aggregations for KPIs
   - `gold_delivery_by_region`: Regional performance metrics
   - `gold_delivery_by_gift_type`: Gift type analysis
   - `gold_overall_progress`: Cumulative statistics
   - `gold_top_cities`: City-level delivery rankings

## 📊 Real-time Dashboard Metrics

The pipeline powers a real-time dashboard showing:

- **Overall KPIs**
  - Total deliveries and gifts delivered
  - Delivery completion percentage
  - Average time to delivery
  - Success vs. delay rates

- **Geographic Analysis**
  - Deliveries by region/country/city
  - Distance traveled
  - Route efficiency

- **Performance Metrics**
  - Delivery time distributions
  - Gift type performance
  - Weather impact analysis
  - Reindeer speed and magic level tracking

- **Live Activity**
  - Recent delivery stream
  - Status breakdown (delivered/en_route/delayed)
  - Geographic heatmap

## 🚀 Setup Instructions

### Prerequisites

- Databricks workspace (AWS, Azure, or GCP)
- DBR 13.3+ with Photon enabled
- Delta Live Tables enabled

### Step 1: Upload Notebooks

1. Import the following files to your Databricks workspace:
   - `data_generator.py` - Generates streaming delivery events
   - `santa_delivery_dlt_pipeline.py` - DLT pipeline definition

### Step 2: Start Data Generation

1. Open `data_generator.py` notebook
2. Configure widgets (or use defaults):
   ```python
   output_path = "/tmp/santa_deliveries"
   events_per_batch = 50
   batch_interval_seconds = 5
   ```
3. Run all cells to start generating streaming data
4. Let it run continuously (stop anytime with interrupt)

### Step 3: Create DLT Pipeline

#### Option A: Using Databricks UI

1. Navigate to **Workflows** → **Delta Live Tables**
2. Click **Create Pipeline**
3. Configure:
   - **Pipeline Name**: `santa_delivery_pipeline`
   - **Product Edition**: Advanced
   - **Pipeline Mode**: Continuous
   - **Notebook Libraries**: Add `santa_delivery_dlt_pipeline.py`
   - **Target**: `santa_delivery_db`
   - **Storage Location**: `/Users/{your_username}/santa_delivery_pipeline`
   - **Configuration**:
     - Key: `source_path`
     - Value: `/tmp/santa_deliveries` (must match data generator output)
   - **Cluster**: 
     - Workers: 2
     - Photon: Enabled
     - Runtime: 13.3 LTS or higher

4. Click **Create**
5. Click **Start** to begin processing

#### Option B: Using REST API

```bash
curl -X POST \
  https://<databricks-instance>/api/2.0/pipelines \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @pipeline_config.json
```

### Step 4: Create Dashboard

1. Navigate to **SQL Workspace** → **Dashboards**
2. Create a new dashboard: "Santa's Delivery Real-time Dashboard"
3. Add queries from `dashboard_queries.sql`:

#### Recommended Visualizations

**Query 1 - Overall Progress**: Counter/KPI cards
- Success Rate %
- Total Deliveries
- Avg Delivery Time
- Total Distance

**Query 2 - Completion Trend**: Line chart over time

**Query 3 - Deliveries by Region**: Bar chart

**Query 4 - Gift Type Performance**: Horizontal bar chart

**Query 5 - Top Cities**: Table with bar chart overlay

**Query 6 - Live Activity Stream**: Table (auto-refresh 10s)

**Query 7 - Delivery Time Distribution**: Histogram

**Query 8 - Weather Impact**: Pie chart

**Query 9 - Distance Over Time**: Area chart

**Query 10 - Reindeer Performance**: Gauge/KPI

**Query 11 - Success vs Delay**: Dual-axis line chart

**Query 12 - Geographic Heatmap**: Map visualization

**Query 13 - Status Breakdown**: Stacked bar

4. Set dashboard auto-refresh to 10-30 seconds for real-time updates

## 🎯 Key Features

### Declarative Pipeline Logic

The pipeline uses Delta Live Tables declarative syntax:

```python
@dlt.table(
    name="silver_santa_deliveries",
    comment="Cleaned and enriched delivery events",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_delivery_id", "delivery_id IS NOT NULL")
def silver_santa_deliveries():
    return (
        dlt.read_stream("bronze_santa_deliveries")
            .withColumn("delivery_timestamp", to_timestamp("timestamp"))
            # ... transformations
    )
```

### Data Quality Expectations

Built-in data quality checks:
- Valid delivery IDs and timestamps
- Coordinate range validation
- Status value constraints
- Positive gift counts

### Streaming Aggregations

Uses Spark Structured Streaming with watermarks:
- Tumbling windows (1, 5, 10, 15 minute intervals)
- Late arrival handling
- Stateful aggregations

## 📁 Project Structure

```
holiday-demo/
├── data_generator.py              # Streaming data simulator
├── santa_delivery_dlt_pipeline.py # DLT pipeline definition
├── dashboard_queries.sql          # SQL queries for dashboard
├── pipeline_config.json           # DLT pipeline configuration
└── README.md                      # This file
```

## 🔧 Configuration Options

### Data Generator Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `output_path` | `/tmp/santa_deliveries` | Delta table location |
| `checkpoint_path` | `/tmp/santa_deliveries_checkpoint` | Streaming checkpoint |
| `events_per_batch` | 50 | Events generated per batch |
| `batch_interval_seconds` | 5 | Seconds between batches |

### Pipeline Configuration

Modify `pipeline_config.json` or UI settings:
- **Cluster size**: Adjust `num_workers` based on throughput
- **Source path**: Must match data generator output
- **Target database**: Schema for output tables
- **Continuous mode**: Enable for real-time processing

## 📈 Sample Metrics

After running for 10 minutes, expect:
- **~6,000** delivery events
- **~600,000** gifts delivered
- **80-85%** success rate
- **30+** cities visited across 6 regions
- **~50,000 km** total distance traveled

## 🐛 Troubleshooting

### Pipeline not processing data
- Verify data generator is running
- Check `source_path` matches in both generator and pipeline
- Confirm pipeline is in "Continuous" mode

### No data in dashboard
- Wait 2-3 minutes for initial aggregations
- Verify queries reference correct database (`santa_delivery_db`)
- Check DLT pipeline status for errors

### High latency
- Increase cluster size
- Enable Photon acceleration
- Reduce aggregation window sizes

## 🎓 Learning Objectives

This project demonstrates:
1. **Delta Live Tables**: Declarative ETL with automatic dependency management
2. **Medallion Architecture**: Bronze/Silver/Gold data quality layers
3. **Structured Streaming**: Real-time data processing with watermarks
4. **Data Quality**: Expectations and validations
5. **Window Aggregations**: Time-based analytics
6. **Real-time Dashboards**: Streaming visualizations

## 🎅 Customization Ideas

- Add more cities/routes
- Implement route optimization algorithms
- Add anomaly detection for unusual delays
- Create predictive models for delivery times
- Integrate with external weather APIs
- Add multi-sleigh tracking
- Implement delivery priority queues

## 📝 Notes

- This is a demonstration project simulating data
- Designed for learning Databricks streaming concepts
- Uses synthetic data generation (not production data)
- Optimized for small-to-medium data volumes

## 🎁 Happy Streaming!

Enjoy exploring Santa's delivery operations with this real-time streaming pipeline! 🎄✨

