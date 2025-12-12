"""
Dashboard Widget Configurations

Copy these configurations when creating widgets in Databricks SQL Dashboard.
Each section represents a visualization widget.
"""

# ============================================================================
# WIDGET 1: Success Rate KPI
# ============================================================================
# Type: Counter
# Query: Query 1 (modified for single metric)
# Refresh: 10 seconds

"""
SQL:
SELECT 
  ROUND(success_rate_percentage, 1) as value
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

Visualization Settings:
- Type: Counter
- Label: "Delivery Success Rate"
- Suffix: "%"
- Target Value: 85
- Color Scheme: Green (>80%), Yellow (70-80%), Red (<70%)
"""

# ============================================================================
# WIDGET 2: Total Deliveries KPI
# ============================================================================
# Type: Counter

"""
SQL:
SELECT 
  period_deliveries as value
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

Visualization Settings:
- Type: Counter
- Label: "Total Deliveries (10-min window)"
- Format: Number with commas
- Icon: 🎁
"""

# ============================================================================
# WIDGET 3: Average Delivery Time KPI
# ============================================================================
# Type: Counter

"""
SQL:
SELECT 
  ROUND(avg_time_to_delivery_minutes, 1) as value
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

Visualization Settings:
- Type: Counter
- Label: "Avg Delivery Time"
- Suffix: " min"
- Target: 0.75
- Color: Blue
"""

# ============================================================================
# WIDGET 4: Total Distance KPI
# ============================================================================
# Type: Counter

"""
SQL:
SELECT 
  ROUND(period_distance_km, 0) as value
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

Visualization Settings:
- Type: Counter
- Label: "Distance Traveled (10-min)"
- Suffix: " km"
- Format: Number with commas
"""

# ============================================================================
# WIDGET 5: Completion Trend Over Time
# ============================================================================
# Type: Line Chart

"""
SQL:
SELECT 
  window_start as time,
  ROUND(completion_percentage, 2) as success_rate,
  ROUND((delayed_deliveries * 100.0 / total_deliveries), 2) as delay_rate
FROM gold_delivery_summary_realtime
ORDER BY window_start ASC
LIMIT 60

Visualization Settings:
- Type: Line Chart
- X-axis: time (Time format)
- Y-axis: success_rate, delay_rate
- Y-axis Label: "Percentage (%)"
- Legend: Show
- Series 1 (success_rate): Green
- Series 2 (delay_rate): Red
- Smooth: Yes
"""

# ============================================================================
# WIDGET 6: Deliveries by Region
# ============================================================================
# Type: Bar Chart

"""
SQL:
WITH latest_window AS (
  SELECT MAX(window_start) as max_window
  FROM gold_delivery_by_region
)
SELECT 
  r.region,
  r.total_deliveries,
  r.total_gifts,
  ROUND(r.success_rate_percentage, 1) as success_rate
FROM gold_delivery_by_region r
INNER JOIN latest_window lw ON r.window_start = lw.max_window
ORDER BY r.total_deliveries DESC

Visualization Settings:
- Type: Bar Chart
- X-axis: region
- Y-axis: total_deliveries
- Color: By success_rate (gradient)
- Sort: Descending
- Show values: Yes
"""

# ============================================================================
# WIDGET 7: Gift Type Performance
# ============================================================================
# Type: Horizontal Bar Chart

"""
SQL:
WITH latest_window AS (
  SELECT MAX(window_start) as max_window
  FROM gold_delivery_by_gift_type
)
SELECT 
  g.gift_type,
  g.total_deliveries,
  ROUND(g.avg_delivery_time, 1) as avg_time_sec
FROM gold_delivery_by_gift_type g
INNER JOIN latest_window lw ON g.window_start = lw.max_window
ORDER BY g.total_deliveries DESC

Visualization Settings:
- Type: Horizontal Bar
- Y-axis: gift_type
- X-axis: total_deliveries
- Color: By avg_time_sec (gradient - yellow to red)
- Show values: Yes
- Sort: Descending
"""

# ============================================================================
# WIDGET 8: Top 10 Cities
# ============================================================================
# Type: Table with Bar Chart

"""
SQL:
WITH latest_window AS (
  SELECT MAX(window_start) as max_window
  FROM gold_top_cities
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY t.total_deliveries DESC) as rank,
  t.city,
  t.country,
  t.region,
  t.total_deliveries,
  t.total_gifts,
  ROUND(t.avg_delivery_time, 1) as avg_time_sec
FROM gold_top_cities t
INNER JOIN latest_window lw ON t.window_start = lw.max_window
ORDER BY t.total_deliveries DESC
LIMIT 10

Visualization Settings:
- Type: Table
- Enable: Sorting, Search
- Conditional Formatting:
  - rank 1: Gold background
  - rank 2-3: Silver background
  - total_deliveries: Bar chart in cell
"""

# ============================================================================
# WIDGET 9: Live Activity Stream
# ============================================================================
# Type: Table (Auto-refresh)

"""
SQL:
SELECT 
  DATE_FORMAT(delivery_timestamp, 'HH:mm:ss') as time,
  city,
  country,
  gift_type,
  num_gifts,
  status,
  ROUND(delivery_time_seconds, 0) as time_sec,
  weather_condition as weather
FROM silver_santa_deliveries
ORDER BY delivery_timestamp DESC
LIMIT 50

Visualization Settings:
- Type: Table
- Auto-refresh: 5 seconds
- Row height: Compact
- Conditional Formatting:
  - status = 'delivered': Green
  - status = 'delayed': Red
  - status = 'en_route': Yellow
"""

# ============================================================================
# WIDGET 10: Delivery Time Distribution
# ============================================================================
# Type: Column Chart (Histogram)

"""
SQL:
SELECT 
  CASE 
    WHEN delivery_time_seconds < 30 THEN '0-30s'
    WHEN delivery_time_seconds < 45 THEN '30-45s'
    WHEN delivery_time_seconds < 60 THEN '45-60s'
    WHEN delivery_time_seconds < 90 THEN '60-90s'
    WHEN delivery_time_seconds < 120 THEN '90-120s'
    ELSE '120s+'
  END as time_range,
  COUNT(*) as delivery_count
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 1 HOUR
GROUP BY time_range
ORDER BY 
  CASE time_range
    WHEN '0-30s' THEN 1
    WHEN '30-45s' THEN 2
    WHEN '45-60s' THEN 3
    WHEN '60-90s' THEN 4
    WHEN '90-120s' THEN 5
    ELSE 6
  END

Visualization Settings:
- Type: Column Chart
- X-axis: time_range
- Y-axis: delivery_count
- Color: Blue gradient
- Show values: Yes
"""

# ============================================================================
# WIDGET 11: Weather Impact
# ============================================================================
# Type: Pie Chart

"""
SQL:
SELECT 
  weather_condition,
  COUNT(*) as count,
  ROUND(AVG(delivery_time_seconds), 1) as avg_time
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 1 HOUR
GROUP BY weather_condition
ORDER BY count DESC

Visualization Settings:
- Type: Pie Chart
- Values: count
- Labels: weather_condition
- Show percentages: Yes
- Color scheme: 
  - Clear: Light blue
  - Cloudy: Gray
  - Snowy: White
  - Foggy: Dark gray
"""

# ============================================================================
# WIDGET 12: Distance Traveled Over Time
# ============================================================================
# Type: Area Chart

"""
SQL:
SELECT 
  window_start as time,
  ROUND(total_distance_traveled_km, 1) as distance_km,
  total_deliveries
FROM gold_delivery_summary_realtime
ORDER BY window_start ASC
LIMIT 100

Visualization Settings:
- Type: Area Chart
- X-axis: time (Time format)
- Y-axis: distance_km
- Fill: Light blue
- Line: Dark blue
- Smooth: Yes
"""

# ============================================================================
# WIDGET 13: Reindeer Speed Gauge
# ============================================================================
# Type: Counter (styled as gauge)

"""
SQL:
SELECT 
  ROUND(avg_reindeer_speed, 0) as value
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

Visualization Settings:
- Type: Counter
- Label: "Avg Reindeer Speed"
- Suffix: " km/h"
- Target Range: 800-1200
- Color: Green (within range)
"""

# ============================================================================
# WIDGET 14: Magic Level Indicator
# ============================================================================
# Type: Counter (as progress bar)

"""
SQL:
SELECT 
  ROUND(avg_magic_level * 100, 1) as value
FROM gold_overall_progress
ORDER BY window_start DESC
LIMIT 1

Visualization Settings:
- Type: Counter
- Label: "Magic Level"
- Suffix: "%"
- Target: 85
- Color: Purple/Sparkle theme
"""

# ============================================================================
# WIDGET 15: Geographic Heatmap
# ============================================================================
# Type: Map

"""
SQL:
SELECT 
  city,
  latitude as lat,
  longitude as lon,
  COUNT(*) as delivery_count,
  SUM(num_gifts) as total_gifts
FROM silver_santa_deliveries
WHERE delivery_timestamp >= current_timestamp() - INTERVAL 30 MINUTES
GROUP BY city, latitude, longitude
ORDER BY delivery_count DESC

Visualization Settings:
- Type: Map
- Latitude: lat
- Longitude: lon
- Size: delivery_count
- Color: By total_gifts (heat gradient)
- Tooltip: city, delivery_count, total_gifts
- Clustering: Enabled
- Base map: Dark theme
"""

# ============================================================================
# DASHBOARD LAYOUT RECOMMENDATION
# ============================================================================
"""
Row 1 (KPIs):
  [Widget 2]  [Widget 1]  [Widget 3]  [Widget 4]
  Total       Success     Avg Time    Distance

Row 2 (Main Charts):
  [Widget 5 - Full Width]
  Completion Trend Over Time

Row 3 (Regional Analysis):
  [Widget 6 - 60%]        [Widget 11 - 40%]
  By Region              Weather Impact

Row 4 (Performance):
  [Widget 7 - 50%]        [Widget 10 - 50%]
  Gift Types             Time Distribution

Row 5 (Details):
  [Widget 8 - Full Width]
  Top 10 Cities

Row 6 (Real-time):
  [Widget 9 - Full Width]
  Live Activity Stream

Row 7 (Advanced):
  [Widget 15 - 70%]       [Widget 13, 14 - 30%]
  Heatmap                Metrics

Auto-refresh: 10-30 seconds for all widgets
Theme: Dark mode recommended
Full screen: Enable for operations center view
"""

# ============================================================================
# EXPORT/IMPORT INSTRUCTIONS
# ============================================================================
"""
To share this dashboard:

1. Export from Databricks SQL:
   - Open dashboard
   - Click "..." menu
   - Select "Export"
   - Save as JSON

2. Import to another workspace:
   - Go to Dashboards
   - Click "Import"
   - Upload JSON file
   - Adjust data source/schema names if needed

3. Schedule email delivery:
   - Dashboard settings
   - Add schedule (e.g., hourly snapshot)
   - Configure recipients
"""

