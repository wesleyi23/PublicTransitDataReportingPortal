# Generated by Django 2.1.7 on 2019-03-27 23:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0004_auto_20190327_1603'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='random_field',
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
