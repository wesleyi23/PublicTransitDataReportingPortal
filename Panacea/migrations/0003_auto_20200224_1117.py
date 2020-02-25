# Generated by Django 2.2.6 on 2020-02-24 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0002_auto_20200221_1507'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense_source',
            name='agency_classification',
            field=models.ManyToManyField(blank=True, to='Panacea.summary_organization_type'),
        ),
        migrations.AddField(
            model_name='fund_balance_type',
            name='agency_classification',
            field=models.ManyToManyField(blank=True, to='Panacea.summary_organization_type'),
        ),
    ]
