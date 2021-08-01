# Generated by Django 2.2.13 on 2021-06-16 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0003_organization_wsdot_managed_ntd_reporter'),
    ]

    operations = [
        migrations.CreateModel(
            name='report_summary_table_subpart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sub_part_type', models.CharField(max_length=100)),
                ('sub_heading', models.CharField(max_length=100)),
                ('sql_query', models.TextField(default=None)),
                ('has_sub_total', models.BooleanField(default=False)),
            ],
        ),
        migrations.AlterField(
            model_name='historicalsummary_report_status',
            name='cover_sheet_status',
            field=models.CharField(choices=[('With user', 'With user'), ('With WSDOT', 'With WSDOT'), ('User approved', 'User approved'), ('Complete', 'Complete')], default='With user', max_length=80),
        ),
        migrations.AlterField(
            model_name='historicalsummary_report_status',
            name='data_report_status',
            field=models.CharField(choices=[('With user', 'With user'), ('With WSDOT', 'With WSDOT'), ('User approved', 'User approved'), ('Complete', 'Complete')], default='With user', max_length=80),
        ),
        migrations.AlterField(
            model_name='summary_report_status',
            name='cover_sheet_status',
            field=models.CharField(choices=[('With user', 'With user'), ('With WSDOT', 'With WSDOT'), ('User approved', 'User approved'), ('Complete', 'Complete')], default='With user', max_length=80),
        ),
        migrations.AlterField(
            model_name='summary_report_status',
            name='data_report_status',
            field=models.CharField(choices=[('With user', 'With user'), ('With WSDOT', 'With WSDOT'), ('User approved', 'User approved'), ('Complete', 'Complete')], default='With user', max_length=80),
        ),
        migrations.CreateModel(
            name='report_summary_table',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_summary_table_type', models.CharField(max_length=100)),
                ('table_heading', models.CharField(max_length=100)),
                ('number_of_years_to_pull', models.IntegerField()),
                ('table_sub_part_list', models.ManyToManyField(to='Panacea.report_summary_table_subpart')),
            ],
        ),
    ]
