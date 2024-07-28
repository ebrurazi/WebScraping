# Generated by Django 4.1.13 on 2024-03-12 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('authors', models.CharField(max_length=255)),
                ('publication_type', models.CharField(max_length=100)),
                ('publication_date', models.DateField()),
                ('publisher_name', models.CharField(max_length=255)),
                ('keywords', models.TextField()),
                ('abstract', models.TextField()),
                ('references', models.TextField()),
                ('citation_count', models.IntegerField()),
                ('doi', models.CharField(blank=True, max_length=100, null=True)),
                ('url', models.URLField()),
            ],
        ),
    ]