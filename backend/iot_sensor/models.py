from django.db import models

class Log(models.Model):
  timestamp = models.DateTimeField(db_index=True, unique=False)
  temperature = models.FloatField(null=True)
  humidity = models.FloatField(null=True)
  air_quality = models.FloatField(null=True)