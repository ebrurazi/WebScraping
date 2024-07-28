from django.db import models
from datetime import date

class Publication(models.Model):
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=255)
    publish_date = models.DateField()
    citation_count = models.IntegerField(default=0)
    publication_type = models.CharField(max_length=100)
    publish_date = models.DateField(default=date.today)
    publisher_name = models.CharField(max_length=255)
    keywords = models.TextField()
    abstract = models.TextField()
    references = models.TextField()
    citation_count = models.IntegerField()
    doi = models.CharField(max_length=100, blank=True, null=True)
    url = models.URLField()
