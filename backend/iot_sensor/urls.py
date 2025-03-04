from django.urls import path, include

from iot_sensor.controller.main import ingest_data, aggregated, processed_data

urlpatterns = [
    path("data", ingest_data, name="ingest_data"),
    path("aggregated", aggregated, name="aggregated"),
    path("processed", processed_data, name="processed"),
]