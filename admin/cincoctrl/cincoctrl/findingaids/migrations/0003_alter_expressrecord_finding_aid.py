# Generated by Django 5.0.9 on 2024-11-06 17:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('findingaids', '0002_remove_supplementaryfile_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expressrecord',
            name='finding_aid',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='findingaids.findingaid'),
        ),
    ]