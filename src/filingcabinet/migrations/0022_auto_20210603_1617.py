# Generated by Django 3.1.8 on 2021-06-03 14:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("filingcabinet", "0021_auto_20210511_1546"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="content_hash",
            field=models.CharField(
                blank=True, editable=False, max_length=40, null=True
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="published_at",
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name="document",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="filingcabinet_document",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(
                condition=models.Q(content_hash__isnull=False),
                fields=["content_hash"],
                name="fc_document_chash_idx",
            ),
        ),
    ]
