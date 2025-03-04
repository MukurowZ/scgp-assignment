import csv
import io
import numpy as np
from scipy import stats
from collections import defaultdict
from django.db.models import Avg, Min, Max, FloatField, F
from django.db.models.functions import Cast
from django.http import JsonResponse, HttpResponse, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from enum import Enum

from iot_sensor.models import Log


class SensorType(Enum):
  TEMPERATURE = "temperature"
  HUMIDITY = "humidity"
  AIR_QUALITY = "air_quality"

@csrf_exempt
def ingest_data(request):
  if request.method != "POST":
    return HttpResponse("This route support only POST request.")

  file = request.FILES.get("file")
  if not file:
    return HttpResponse("Please upload file.")

  if not file.name.endswith(".csv"): 
    # Check if file is CSV
    return JsonResponse({"error": "Invalid file format. Please upload a CSV file."}, status=400)

  decoded_file = file.read().decode("utf-8")
  csv_reader = csv.reader(io.StringIO(decoded_file), delimiter=",")

  # Skip header row
  next(csv_reader, None)

  # Import all the data, no matter it duplicate timestamps or not
  # At the end there has endpoint to get clean data.
  logs_to_create = []
  for row in csv_reader:
    try:
      timestamp = parse_datetime(row[0])
      temperature = float(row[1]) if row[1] else None
      humidity = float(row[2]) if row[2] else None
      air_quality = float(row[3]) if row[3] else None

      logs_to_create.append(Log(
        timestamp=timestamp,
        temperature=temperature,
        humidity=humidity,
        air_quality=air_quality
      ))
    except (ValueError, IndexError, ValidationError) as e:
      return JsonResponse({"error": f"Invalid data format in row: {row}, error: {str(e)}"}, status=400)

  Log.objects.bulk_create(logs_to_create)

  return JsonResponse({"message": f"Records processed successfully!"})


@csrf_exempt
def aggregated(request):
  if request.method != "GET":
      return HttpResponse("This route supports only GET request.")

  # Get query parameters
  query = QueryDict(request.GET.urlencode())
  from_timestamp = query.get("from")
  to_timestamp = query.get("to")

  filters = {}
  if from_timestamp:
    filters["timestamp__gte"] = parse_datetime(from_timestamp)
  if to_timestamp:
    filters["timestamp__lte"] = parse_datetime(to_timestamp)

  logs = Log.objects.filter(**filters)

  # To get min/max timestamp for each field
  def get_timestamp(value, field):
    if value is not None:
      log_entry = logs.filter(**{field: value}).order_by("timestamp").first()
      return log_entry.timestamp if log_entry else None
    return None

  # To calculate median on each columns and get the timestamp immedietly
  def get_median(values, field):
    if not values:
      return None, None
    median_value = float(np.median(values))
    median_entry = logs.filter(**{f"{field}__gte": median_value}).order_by("timestamp").first()
    return median_value, median_entry.timestamp if median_entry else None

  # Aggregate mean, min, max values
  stats = logs.aggregate(
    temperature_avg=Avg(Cast("temperature", FloatField())),
    temperature_min=Min("temperature"),
    temperature_max=Max("temperature"),
    humidity_avg=Avg(Cast("humidity", FloatField())),
    humidity_min=Min("humidity"),
    humidity_max=Max("humidity"),
    air_quality_avg=Avg(Cast("air_quality", FloatField())),
    air_quality_min=Min("air_quality"),
    air_quality_max=Max("air_quality"),
  )

  stats["temperature_min_timestamp"] = get_timestamp(stats["temperature_min"], "temperature")
  stats["temperature_max_timestamp"] = get_timestamp(stats["temperature_max"], "temperature")
  stats["humidity_min_timestamp"] = get_timestamp(stats["humidity_min"], "humidity")
  stats["humidity_max_timestamp"] = get_timestamp(stats["humidity_max"], "humidity")
  stats["air_quality_min_timestamp"] = get_timestamp(stats["air_quality_min"], "air_quality")
  stats["air_quality_max_timestamp"] = get_timestamp(stats["air_quality_max"], "air_quality")

  # Prepare & Get median values and timestamp
  temperature_values = list(logs.values_list("temperature", flat=True).exclude(temperature__isnull=True))
  humidity_values = list(logs.values_list("humidity", flat=True).exclude(humidity__isnull=True))
  air_quality_values = list(logs.values_list("air_quality", flat=True).exclude(air_quality__isnull=True))
  stats["temperature_median"], stats["temperature_median_timestamp"] = get_median(temperature_values, "temperature")
  stats["humidity_median"], stats["humidity_median_timestamp"] = get_median(humidity_values, "humidity")
  stats["air_quality_median"], stats["air_quality_median_timestamp"] = get_median(air_quality_values, "air_quality")

  return JsonResponse(stats, safe=False)




@csrf_exempt
def processed_data(request):
  total_logs = Log.objects.count()

  def advanced_filter(sensor: SensorType):
    all_logs = Log.objects.exclude(
      **{f"{sensor.value}__isnull": True}
    )

    # Convert to list of values and timestamps
    sensor_data = [
      {"value": float(getattr(log, sensor.value)), "timestamp": log.timestamp} 
      for log in all_logs 
      if getattr(log, sensor.value) is not None
    ]

    if not sensor_data:
      return {"processed_data": [], "anomalies": [], "stats": {}}

    sensorValues = [item["value"] for item in sensor_data]

    # IQR Method
    Q1 = float(np.percentile(sensorValues, 25))
    Q3 = float(np.percentile(sensorValues, 75))
    IQR = Q3 - Q1
    lower_bound = float(Q1 - 1.5 * IQR)
    upper_bound = float(Q3 + 1.5 * IQR)

    z_scores = np.abs(stats.zscore(sensorValues))

    # Identify anomalies
    anomalies = []
    for _, (data_point, z_score) in enumerate(zip(sensor_data, z_scores)):
      is_iqr_anomaly = (
        data_point["value"] < lower_bound or 
        data_point["value"] > upper_bound
      )
      is_z_score_anomaly = z_score > 3

      if is_iqr_anomaly or is_z_score_anomaly:
        anomalies.append({
          "timestamp": str(data_point["timestamp"]),
          "value": float(data_point["value"]),
          "z_score": float(z_score),
          "is_iqr_anomaly": bool(is_iqr_anomaly),
          "is_z_score_anomaly": bool(is_z_score_anomaly)
        })

    return {
      "processed_data": [
        {
          "timestamp": str(item["timestamp"]),
          "value": float(item["value"])
        } for item in sensor_data
      ],
      "anomalies": anomalies,
      "stats": {
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "total_points": len(sensor_data),
        "anomaly_count": len(anomalies)
      }
    }

  processed_temperature = advanced_filter(SensorType.TEMPERATURE)
  processed_humidity = advanced_filter(SensorType.HUMIDITY)
  processed_air_quality = advanced_filter(SensorType.AIR_QUALITY)

  return JsonResponse({
    "total_logs": total_logs,
    "temperature": processed_temperature,
    "humidity": processed_humidity,
    "air_quality": processed_air_quality,
  })