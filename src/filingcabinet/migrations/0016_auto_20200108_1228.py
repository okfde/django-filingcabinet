# Generated by Django 2.2.4 on 2020-01-08 11:28

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("filingcabinet", "0015_auto_20191030_1840"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentPortal",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=250)),
                ("slug", models.SlugField(max_length=250)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("public", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "document portal",
                "verbose_name_plural": "document portals",
            },
        ),
        migrations.AlterModelOptions(
            name="pageannotation",
            options={"ordering": ("-timestamp",)},
        ),
        migrations.AddField(
            model_name="document",
            name="portal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="filingcabinet.DocumentPortal",
            ),
        ),
        migrations.AddField(
            model_name="documentcollection",
            name="portal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="filingcabinet.DocumentPortal",
            ),
        ),
    ]
