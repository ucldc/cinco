# Generated by Django 5.0.9 on 2025-03-27 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('findingaids', '0008_indexinghistory'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='findingaid',
            options={'ordering': ['collection_title']},
        ),
        migrations.AlterField(
            model_name='expressrecord',
            name='language',
            field=models.ManyToManyField(to='findingaids.language'),
        ),
        migrations.AlterField(
            model_name='findingaid',
            name='status',
            field=models.CharField(choices=[('started', 'Started'), ('queued_preview', 'Queued for Preview'), ('previewed', 'Previewed'), ('preview_error', 'Preview Error'), ('queued_publish', 'Queued for Publication'), ('published', 'Published'), ('publish_error', 'Publication Error')], default='started', max_length=50),
        ),
    ]
