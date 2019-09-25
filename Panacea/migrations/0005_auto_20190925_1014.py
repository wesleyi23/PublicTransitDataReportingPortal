# Generated by Django 2.2b1 on 2019-09-25 17:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Panacea', '0004_auto_20190925_1011'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpensesSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specific_expense_source', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='RevenueSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specific_revenue_source', models.CharField(max_length=200)),
            ],
        ),
        migrations.AlterField(
            model_name='historicalsummaryexpenses',
            name='specific_expense_source',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='Panacea.ExpensesSource'),
        ),
        migrations.AlterField(
            model_name='historicalsummaryexpenses',
            name='specific_expense_value',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='historicalsummaryrevenues',
            name='specific_revenue_source',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='Panacea.RevenueSource'),
        ),
        migrations.AlterField(
            model_name='historicalsummaryrevenues',
            name='specific_revenue_value',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='summaryexpenses',
            name='specific_expense_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='Panacea.ExpensesSource'),
        ),
        migrations.AlterField(
            model_name='summaryexpenses',
            name='specific_expense_value',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='summaryrevenues',
            name='specific_revenue_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='Panacea.RevenueSource'),
        ),
        migrations.AlterField(
            model_name='summaryrevenues',
            name='specific_revenue_value',
            field=models.FloatField(),
        ),
    ]
