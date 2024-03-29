# Generated by Django 3.0.7 on 2020-06-22 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("filingcabinet", "0017_auto_20200514_1329"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="collectiondirectory",
            options={
                "verbose_name": "Collection directory",
                "verbose_name_plural": "Collection directories",
            },
        ),
        migrations.AddField(
            model_name="document",
            name="outline",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="document",
            name="properties",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
