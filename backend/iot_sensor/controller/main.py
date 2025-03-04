import csv
import io
import numpy as np
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

  # Get median values and timestamp
  temperature_values = list(logs.values_list("temperature", flat=True).exclude(temperature__isnull=True))
  humidity_values = list(logs.values_list("humidity", flat=True).exclude(humidity__isnull=True))
  air_quality_values = list(logs.values_list("air_quality", flat=True).exclude(air_quality__isnull=True))

  # Get median values and timestamp
  stats["temperature_median"], stats["temperature_median_timestamp"] = get_median(temperature_values, "temperature")
  stats["humidity_median"], stats["humidity_median_timestamp"] = get_median(humidity_values, "humidity")
  stats["air_quality_median"], stats["air_quality_median_timestamp"] = get_median(air_quality_values, "air_quality")

  return JsonResponse(stats, safe=False)

def processed_data(request):
  totalLogs = Log.objects.count()

  def iqr_filter(sensor: SensorType):
    # Fetch sensor values, ensure they are numbers
    sensorValues = [
      float(value) for value in Log.objects.exclude(
        **{f"{sensor.value}__isnull": True}
      ).values_list(sensor.value, flat=True) if value is not None
    ]

    if not sensorValues:
      return []

    # Compute Q1, Q3, IQR, lower & upper bounds
    Q1 = np.percentile(sensorValues, 25)
    Q3 = np.percentile(sensorValues, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Fetch filtered logs within IQR range and ordered by timestamp
    logs = Log.objects.filter(
      **{
        f"{sensor.value}__gte": lower_bound,
        f"{sensor.value}__lte": upper_bound,
      }
    ).order_by("timestamp")

    # Begin to remove duplicates based on timestamp, keeping the most complete entry
    seen_timestamps = defaultdict(list)
    for log in logs:
      seen_timestamps[log.timestamp].append(log)

    deduplicated_logs = []
    for timestamp, logs_with_same_timestamp in seen_timestamps.items():
      # Logic for most complete: Example: pick the record with the most non-null fields
      most_complete_log = max(
        logs_with_same_timestamp,
        # This lambda fn will focus only "sensor.value" field, will ignore the rest
        key=lambda log: sum(1 for field in [sensor.value, 'timestamp'] if getattr(log, field) is not None)
      )
      deduplicated_logs.append(most_complete_log)

    # Map to get only 
    result = [
      {"timestamp": getattr(log, "timestamp"), "value": getattr(log, sensor.value)} for log in deduplicated_logs
    ]

    return result

  processed_temperature = iqr_filter(SensorType.TEMPERATURE)
  processed_humidity = iqr_filter(SensorType.HUMIDITY)
  processed_air_quality = iqr_filter(SensorType.AIR_QUALITY)

  return JsonResponse({
      "totalLogs": totalLogs,
      "temperature": processed_temperature,
      "humidity": processed_humidity,
      "air_quality": processed_air_quality,
  })