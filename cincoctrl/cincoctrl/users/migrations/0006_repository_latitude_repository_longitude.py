# Generated by Django 5.0.9 on 2025-03-04 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_merge_20250212_0843'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
