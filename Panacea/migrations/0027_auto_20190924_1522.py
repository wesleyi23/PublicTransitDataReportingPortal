# Generated by Django 2.2.5 on 2019-09-24 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0026_auto_20190924_1416'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cover_sheet',
            name='organization_logo',
            field=models.ImageField(blank=True, null=True, upload_to='Organization_logo'),
        ),
    ]
