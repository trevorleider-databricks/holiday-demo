# Architecture & Data Flow

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA GENERATION LAYER                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  data_generator.py (Simulates Santa's Sleigh)              │    │
│  │  • 30+ global cities                                        │    │
│  │  • 7 gift types                                             │    │
│  │  • Weather conditions                                       │    │
│  │  • Realistic delivery patterns                             │    │
│  └───────────────────────┬────────────────────────────────────┘    │
└────────────────────────────┼────────────────────────────────────────┘
                             │ Writes events continuously
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BRONZE LAYER (Raw Ingestion)                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  bronze_santa_deliveries                                    │    │
│  │  • Raw event capture                                        │    │
│  │  • No transformations                                       │    │
│  │  • Ingestion timestamp added                               │    │
│  │  • Full audit trail                                        │    │
│  └───────────────────────┬────────────────────────────────────┘    │
└────────────────────────────┼────────────────────────────────────────┘
                             │ Streaming read
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SILVER LAYER (Cleaned & Enriched)                  │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  silver_santa_deliveries                                    │    │
│  │  ✓ Data quality checks                                     │    │
│  │  ✓ Type conversions (timestamp, date)                      │    │
│  │  ✓ Calculated fields:                                      │    │
│  │    - Performance indicators (is_delivered, is_delayed)     │    │
│  │    - Effective speed calculations                          │    │
│  │    - Weather impact factors                                │    │
│  │    - Adjusted delivery times                               │    │
│  │  ✓ Validation rules enforced                               │    │
│  └───────────────────────┬────────────────────────────────────┘    │
└────────────────────────────┼────────────────────────────────────────┘
                             │ Multiple streaming aggregations
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   GOLD LAYER (Business Metrics)                      │
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │ gold_delivery_       │  │ gold_delivery_       │                │
│  │ summary_realtime     │  │ by_region            │                │
│  │ • 1-min windows      │  │ • 5-min windows      │                │
│  │ • Overall KPIs       │  │ • Regional stats     │                │
│  │ • Success rates      │  │ • Geographic perf    │                │
│  └──────────────────────┘  └──────────────────────┘                │
│                                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │ gold_delivery_       │  │ gold_overall_        │                │
│  │ by_gift_type         │  │ progress             │                │
│  │ • 5-min windows      │  │ • 10-min windows     │                │
│  │ • Gift type metrics  │  │ • Cumulative stats   │                │
│  │ • Time analysis      │  │ • Weather breakdown  │                │
│  └──────────────────────┘  └──────────────────────┘                │
│                                                                       │
│  ┌──────────────────────┐                                           │
│  │ gold_top_cities      │                                           │
│  │ • 15-min windows     │                                           │
│  │ • City rankings      │                                           │
│  │ • Volume analysis    │                                           │
│  └──────────────────────┘                                           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ SQL queries
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    VISUALIZATION LAYER                                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Databricks SQL Dashboard                                   │    │
│  │  • 14 pre-built queries                                     │    │
│  │  • Real-time KPI cards                                      │    │
│  │  • Time-series charts                                       │    │
│  │  • Geographic heatmaps                                      │    │
│  │  • Live activity stream                                     │    │
│  │  • Auto-refresh (10-30 seconds)                            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Details

### Event Generation → Bronze
- **Frequency**: Configurable (default: 50 events every 5 seconds)
- **Format**: Delta Lake (parquet + transaction log)
- **Partitioning**: By ingestion date
- **Schema**: Strictly enforced with StructType

### Bronze → Silver
- **Processing**: Spark Structured Streaming with DLT
- **Quality Gates**: 5 data quality expectations
  - ✓ Valid delivery_id
  - ✓ Valid timestamp
  - ✓ Status in allowed values
  - ✓ Coordinates within valid ranges
  - ✓ Positive gift counts
- **Transformations**:
  - String timestamps → proper Timestamp type
  - Add date/hour/minute extractions
  - Calculate performance flags
  - Compute weather impact
  - Derive speed metrics

### Silver → Gold
- **Aggregation Strategy**: Multiple time windows
  - 1-minute: Real-time KPIs
  - 5-minute: Regional & gift type analysis
  - 10-minute: Overall progress
  - 15-minute: City rankings
- **Watermarking**: 5-minute watermark for late data
- **State Management**: Managed by Spark Structured Streaming
- **Updates**: Continuous with micro-batches

## 🎯 Key Design Patterns

### 1. Medallion Architecture
- **Bronze**: "Just land it" - preserve raw data
- **Silver**: "Clean it once" - single source of truth
- **Gold**: "Serve it fast" - pre-aggregated for queries

### 2. Data Quality as Code
```python
@dlt.expect_or_drop("valid_status", "status IN ('en_route', 'delivered', 'delayed')")
```
- Declarative quality rules
- Automatic metrics collection
- Bad records isolated and tracked

### 3. Streaming Windows
```python
.groupBy(window("delivery_timestamp", "1 minute"))
.withWatermark("delivery_timestamp", "5 minutes")
```
- Tumbling windows for consistent time buckets
- Watermark handles late-arriving events
- Trade-off: latency vs. completeness

### 4. Enrichment at Silver
- Calculate once, use many times
- Derived metrics available to all gold tables
- Consistent business logic

## 📊 Performance Characteristics

### Throughput
- **Input**: ~600 events/min (default config)
- **Processing**: Sub-second latency Bronze → Silver
- **Aggregation**: 1-minute end-to-end latency for Gold

### Scalability
- **Small**: 2 workers handles default load easily
- **Medium**: 4-8 workers for 10x data volume
- **Large**: Auto-scaling for variable loads

### Resource Usage
- **Bronze**: Minimal (simple append)
- **Silver**: Low (streaming transformations)
- **Gold**: Medium (multiple stateful aggregations)

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Storage | Delta Lake | ACID transactions, time travel, schema enforcement |
| Processing | Spark Structured Streaming | Scalable stream processing |
| Orchestration | Delta Live Tables | Declarative ETL, dependency management |
| Quality | DLT Expectations | Data validation, metrics |
| Visualization | Databricks SQL | Interactive dashboards |
| Compute | Photon | Vectorized query engine |

## 🎓 Learning Concepts Demonstrated

1. **Streaming Architecture**: End-to-end real-time pipeline
2. **Declarative ETL**: DLT syntax and conventions
3. **Data Quality**: Expectations and error handling
4. **Window Aggregations**: Time-based analytics
5. **State Management**: Streaming aggregations
6. **Medallion Pattern**: Multi-layer data architecture
7. **Performance Tuning**: Photon, partitioning, z-ordering

## 🚀 Extension Points

Want to enhance the pipeline? Consider:

1. **ML Integration**: Predict delivery delays
2. **Complex Event Processing**: Detect route anomalies
3. **Change Data Capture**: Track status transitions
4. **Real-time Alerting**: Trigger on high delay rates
5. **A/B Testing**: Different routing algorithms
6. **Multi-tenant**: Separate pipelines per region
7. **External Data**: Join with weather APIs
8. **Graph Analytics**: Optimize delivery routes

