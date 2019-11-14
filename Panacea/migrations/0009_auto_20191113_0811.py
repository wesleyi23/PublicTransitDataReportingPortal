# Generated by Django 2.2.6 on 2019-11-13 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0008_auto_20191112_0831'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='revenue_source',
            name='agency_classification',
        ),
        migrations.AddField(
            model_name='revenue_source',
            name='agency_classification',
            field=models.ManyToManyField(blank=True, null=True, to='Panacea.summary_organization_type'),
        ),
    ]
