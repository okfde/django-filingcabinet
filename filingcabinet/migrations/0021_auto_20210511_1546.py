# Generated by Django 3.1.8 on 2021-05-11 13:46

from django.db import migrations, models
import filingcabinet.validators


class Migration(migrations.Migration):

    dependencies = [
        ('filingcabinet', '0020_auto_20210505_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentcollection',
            name='settings',
            field=models.JSONField(blank=True, default=dict, validators=[filingcabinet.validators.validate_settings_schema]),
        ),
        migrations.AlterField(
            model_name='documentportal',
            name='settings',
            field=models.JSONField(blank=True, default=dict, validators=[filingcabinet.validators.validate_settings_schema]),
        ),
    ]