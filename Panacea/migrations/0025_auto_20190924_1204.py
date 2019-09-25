# Generated by Django 2.2.5 on 2019-09-24 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0024_auto_20190924_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cover_sheet',
            name='community_medicaid_days_of_service',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Days of service'),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='community_medicaid_revenue_service_vehicles',
            field=models.TextField(blank=True, null=True, verbose_name='Revenue service vehicles'),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='community_medicaid_service_and_eligibility',
            field=models.TextField(blank=True, null=True, verbose_name='Service and eligibility description'),
        ),
        migrations.AlterField(
            model_name='cover_sheet',
            name='transit_development_plan_url',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Transit development plan URL'),
        ),
    ]
