# Databricks notebook source
# MAGIC %md
# MAGIC # Santa's Delivery Data Generator
# MAGIC This notebook generates streaming data simulating Santa's gift deliveries around the world

# COMMAND ----------

import random
import time
import json
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# COMMAND ----------

# Configuration
dbutils.widgets.text("output_path", "/tmp/santa_deliveries", "Output Path")
dbutils.widgets.text("checkpoint_path", "/tmp/santa_deliveries_checkpoint", "Checkpoint Path")
dbutils.widgets.text("events_per_batch", "50", "Events Per Batch")
dbutils.widgets.text("batch_interval_seconds", "5", "Batch Interval (seconds)")

output_path = dbutils.widgets.get("output_path")
checkpoint_path = dbutils.widgets.get("checkpoint_path")
events_per_batch = int(dbutils.widgets.get("events_per_batch"))
batch_interval = int(dbutils.widgets.get("batch_interval_seconds"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## World Locations and Routes

# COMMAND ----------

# Major cities around the world where Santa delivers gifts
WORLD_LOCATIONS = [
    {"city": "New York", "country": "USA", "region": "North America", "lat": 40.7128, "lon": -74.0060, "timezone": "EST", "population": 8500000},
    {"city": "Los Angeles", "country": "USA", "region": "North America", "lat": 34.0522, "lon": -118.2437, "timezone": "PST", "population": 4000000},
    {"city": "Chicago", "country": "USA", "region": "North America", "lat": 41.8781, "lon": -87.6298, "timezone": "CST", "population": 2700000},
    {"city": "London", "country": "UK", "region": "Europe", "lat": 51.5074, "lon": -0.1278, "timezone": "GMT", "population": 9000000},
    {"city": "Paris", "country": "France", "region": "Europe", "lat": 48.8566, "lon": 2.3522, "timezone": "CET", "population": 2200000},
    {"city": "Berlin", "country": "Germany", "region": "Europe", "lat": 52.5200, "lon": 13.4050, "timezone": "CET", "population": 3600000},
    {"city": "Tokyo", "country": "Japan", "region": "Asia", "lat": 35.6762, "lon": 139.6503, "timezone": "JST", "population": 14000000},
    {"city": "Beijing", "country": "China", "region": "Asia", "lat": 39.9042, "lon": 116.4074, "timezone": "CST", "population": 21500000},
    {"city": "Shanghai", "country": "China", "region": "Asia", "lat": 31.2304, "lon": 121.4737, "timezone": "CST", "population": 27000000},
    {"city": "Mumbai", "country": "India", "region": "Asia", "lat": 19.0760, "lon": 72.8777, "timezone": "IST", "population": 20400000},
    {"city": "Sydney", "country": "Australia", "region": "Oceania", "lat": -33.8688, "lon": 151.2093, "timezone": "AEDT", "population": 5300000},
    {"city": "Melbourne", "country": "Australia", "region": "Oceania", "lat": -37.8136, "lon": 144.9631, "timezone": "AEDT", "population": 5100000},
    {"city": "São Paulo", "country": "Brazil", "region": "South America", "lat": -23.5505, "lon": -46.6333, "timezone": "BRT", "population": 12300000},
    {"city": "Rio de Janeiro", "country": "Brazil", "region": "South America", "lat": -22.9068, "lon": -43.1729, "timezone": "BRT", "population": 6700000},
    {"city": "Buenos Aires", "country": "Argentina", "region": "South America", "lat": -34.6037, "lon": -58.3816, "timezone": "ART", "population": 3100000},
    {"city": "Mexico City", "country": "Mexico", "region": "North America", "lat": 19.4326, "lon": -99.1332, "timezone": "CST", "population": 9200000},
    {"city": "Toronto", "country": "Canada", "region": "North America", "lat": 43.6532, "lon": -79.3832, "timezone": "EST", "population": 2900000},
    {"city": "Vancouver", "country": "Canada", "region": "North America", "lat": 49.2827, "lon": -123.1207, "timezone": "PST", "population": 675000},
    {"city": "Dubai", "country": "UAE", "region": "Middle East", "lat": 25.2048, "lon": 55.2708, "timezone": "GST", "population": 3400000},
    {"city": "Moscow", "country": "Russia", "region": "Europe", "lat": 55.7558, "lon": 37.6173, "timezone": "MSK", "population": 12500000},
    {"city": "Istanbul", "country": "Turkey", "region": "Europe", "lat": 41.0082, "lon": 28.9784, "timezone": "TRT", "population": 15500000},
    {"city": "Cairo", "country": "Egypt", "region": "Africa", "lat": 30.0444, "lon": 31.2357, "timezone": "EET", "population": 20900000},
    {"city": "Lagos", "country": "Nigeria", "region": "Africa", "lat": 6.5244, "lon": 3.3792, "timezone": "WAT", "population": 14400000},
    {"city": "Johannesburg", "country": "South Africa", "region": "Africa", "lat": -26.2041, "lon": 28.0473, "timezone": "SAST", "population": 5700000},
    {"city": "Singapore", "country": "Singapore", "region": "Asia", "lat": 1.3521, "lon": 103.8198, "timezone": "SGT", "population": 5700000},
    {"city": "Seoul", "country": "South Korea", "region": "Asia", "lat": 37.5665, "lon": 126.9780, "timezone": "KST", "population": 9700000},
    {"city": "Bangkok", "country": "Thailand", "region": "Asia", "lat": 13.7563, "lon": 100.5018, "timezone": "ICT", "population": 10700000},
    {"city": "Hong Kong", "country": "China", "region": "Asia", "lat": 22.3193, "lon": 114.1694, "timezone": "HKT", "population": 7500000},
    {"city": "Rome", "country": "Italy", "region": "Europe", "lat": 41.9028, "lon": 12.4964, "timezone": "CET", "population": 2900000},
    {"city": "Madrid", "country": "Spain", "region": "Europe", "lat": 40.4168, "lon": -3.7038, "timezone": "CET", "population": 3200000}
]

# Gift types with relative weights
GIFT_TYPES = [
    {"name": "Toys", "weight": 30, "avg_delivery_time": 45},
    {"name": "Books", "weight": 15, "avg_delivery_time": 30},
    {"name": "Electronics", "weight": 20, "avg_delivery_time": 60},
    {"name": "Clothing", "weight": 15, "avg_delivery_time": 35},
    {"name": "Games", "weight": 12, "avg_delivery_time": 40},
    {"name": "Art Supplies", "weight": 5, "avg_delivery_time": 35},
    {"name": "Sports Equipment", "weight": 3, "avg_delivery_time": 50}
]

# Delivery statuses
DELIVERY_STATUSES = ["en_route", "delivered", "delayed"]
STATUS_WEIGHTS = [0.15, 0.80, 0.05]  # Most deliveries are successful

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper Functions

# COMMAND ----------

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance in kilometers"""
    from math import radians, cos, sin, asin, sqrt
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km

def weighted_random_choice(items, weight_key='weight'):
    """Select item based on weights"""
    weights = [item[weight_key] for item in items]
    return random.choices(items, weights=weights)[0]

def generate_delivery_event(delivery_id, start_time, previous_location=None):
    """Generate a single delivery event"""
    
    # Select destination
    destination = random.choice(WORLD_LOCATIONS)
    
    # Select gift type
    gift_type = weighted_random_choice(GIFT_TYPES)
    
    # Calculate number of gifts based on population (more gifts to larger cities)
    num_gifts = max(1, int(random.gauss(destination["population"] / 100000, 5)))
    
    # Determine status
    status = random.choices(DELIVERY_STATUSES, weights=STATUS_WEIGHTS)[0]
    
    # Calculate delivery time
    base_time = gift_type["avg_delivery_time"]
    delivery_time_seconds = max(10, int(random.gauss(base_time, base_time * 0.3)))
    
    if status == "delayed":
        delivery_time_seconds = int(delivery_time_seconds * random.uniform(1.5, 3.0))
    
    # Calculate distance from previous location
    distance_km = 0
    if previous_location:
        distance_km = calculate_distance(
            previous_location["lat"], previous_location["lon"],
            destination["lat"], destination["lon"]
        )
    
    # Generate timestamp
    timestamp = start_time + timedelta(seconds=random.randint(0, 30))
    
    event = {
        "delivery_id": delivery_id,
        "timestamp": timestamp.isoformat(),
        "city": destination["city"],
        "country": destination["country"],
        "region": destination["region"],
        "latitude": destination["lat"],
        "longitude": destination["lon"],
        "timezone": destination["timezone"],
        "gift_type": gift_type["name"],
        "num_gifts": num_gifts,
        "status": status,
        "delivery_time_seconds": delivery_time_seconds,
        "distance_from_previous_km": round(distance_km, 2),
        "weather_condition": random.choice(["Clear", "Snowy", "Cloudy", "Foggy"]),
        "reindeer_speed_kmh": round(random.uniform(800, 1200), 2),
        "magic_level": round(random.uniform(0.7, 1.0), 2)
    }
    
    return event, destination

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Streaming Data

# COMMAND ----------

def generate_batch_data():
    """Generate a batch of delivery events"""
    events = []
    current_time = datetime.utcnow()
    previous_location = None
    
    # Generate delivery ID prefix based on batch time
    batch_id = int(current_time.timestamp())
    
    for i in range(events_per_batch):
        delivery_id = f"DELIVERY_{batch_id}_{i:05d}"
        event, location = generate_delivery_event(delivery_id, current_time, previous_location)
        events.append(event)
        previous_location = location
        current_time += timedelta(seconds=random.randint(1, 5))
    
    return events

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Data to Delta Lake

# COMMAND ----------

# Define schema for the events
schema = StructType([
    StructField("delivery_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("city", StringType(), False),
    StructField("country", StringType(), False),
    StructField("region", StringType(), False),
    StructField("latitude", DoubleType(), False),
    StructField("longitude", DoubleType(), False),
    StructField("timezone", StringType(), False),
    StructField("gift_type", StringType(), False),
    StructField("num_gifts", IntegerType(), False),
    StructField("status", StringType(), False),
    StructField("delivery_time_seconds", IntegerType(), False),
    StructField("distance_from_previous_km", DoubleType(), False),
    StructField("weather_condition", StringType(), False),
    StructField("reindeer_speed_kmh", DoubleType(), False),
    StructField("magic_level", DoubleType(), False)
])

# COMMAND ----------

print(f"Starting Santa's Delivery Data Generator...")
print(f"Output Path: {output_path}")
print(f"Events per batch: {events_per_batch}")
print(f"Batch interval: {batch_interval} seconds")
print(f"\nGenerating continuous stream... (Stop cell to halt)")

batch_count = 0
try:
    while True:
        # Generate batch of events
        events = generate_batch_data()
        
        # Convert to DataFrame
        df = spark.createDataFrame(events, schema=schema)
        
        # Write to Delta Lake
        df.write \
            .format("delta") \
            .mode("append") \
            .save(output_path)
        
        batch_count += 1
        total_events = batch_count * events_per_batch
        
        if batch_count % 10 == 0:
            print(f"Batch {batch_count}: Generated {total_events} total delivery events")
        
        # Wait before next batch
        time.sleep(batch_interval)
        
except KeyboardInterrupt:
    print(f"\nStopped. Generated {batch_count} batches with {batch_count * events_per_batch} total events.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Data Generation

# COMMAND ----------

# Read the generated data to verify
df_verify = spark.read.format("delta").load(output_path)
print(f"Total records generated: {df_verify.count()}")
display(df_verify.orderBy(col("timestamp").desc()).limit(20))

