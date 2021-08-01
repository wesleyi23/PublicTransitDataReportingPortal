import re

from django.db import connection

from Panacea.models import transit_metrics, revenue_source
from Panacea.utilities import get_current_summary_report_year


class ReportSummaryTable:
    def __init__(self, report_summary_table):
        self.report_summary_table = report_summary_table
        self.table_heading = report_summary_table.table_heading
        self.table_sub_part_list = report_summary_table.table_sub_part_list.all()
        self.number_of_years_to_pull = report_summary_table.number_of_years_to_pull

    def produce_table(self):
        sql_list = []
        for i in self.table_sub_part_list:
            sub_part = ReportSummaryTableSubPart(i)
            sql_list.append(sub_part.return_final_sub_part())
        return sql_list


class ReportSummaryTableSubPart:
    def __init__(self, report_summary_table_subpart):
        self.report_summary_table_subpart = report_summary_table_subpart
        self.sub_heading = report_summary_table_subpart.sub_heading
        self.sql_query = report_summary_table_subpart.sql_query
        self.has_sub_total = report_summary_table_subpart.has_sub_total
        self.sub_total_text = report_summary_table_subpart.sub_total_text
        self.calculate_percentage_change = report_summary_table_subpart.calculate_percentage_change
        self.round_using_form_masking_class = report_summary_table_subpart.round_using_form_masking_class

    def parse_sql_str(self):
        key_word_variables = {
            'year': str(get_current_summary_report_year())
        }
        sql = self.sql_query
        replace = {}
        replace_strings = re.findall('{{[^}]+}}', self.sql_query)
        for i in replace_strings:
            replace_value = i
            replace_value = replace_value.replace("{{", "")
            replace_value = replace_value.replace("}}", "")
            for key, value in key_word_variables.items():
                replace_value = replace_value.replace(key, value)
                replace_value = str(eval(replace_value))
            replace[i] = replace_value
        for key, value in replace.items():
            sql = sql.replace(key, value)
        return sql

    def execute_sql_str(self):
        with connection.cursor() as cursor:
            cursor.execute(self.parse_sql_str())
            return cursor.fetchall()

    @staticmethod
    def remove_none_from_query_results(results):
        for count, item in enumerate(results):
            results[count] = [0 if x is None else x for x in results[count]]
        return results

    def round_query_results_function(self, results):
        float_transit_metrics = transit_metrics.objects.filter(form_masking_class="Float").values_list('name', flat=True)
        int_transit_metrics = transit_metrics.objects.filter(form_masking_class="Int").values_list('name', flat=True)

        for count_i, item_i in enumerate(results):
            if self.calculate_percentage_change:
                rounded_items = item_i[2:-1]
            else:
                rounded_items = item_i[2:]

            if item_i[0] in int_transit_metrics:
                for count_j, item_j in enumerate(rounded_items, start=2):
                    results[count_i][count_j] = round(item_j)
            elif item_i[0] in float_transit_metrics:
                pass
            else:
                for count_j, item_j in enumerate(rounded_items, start=2):
                    results[count_i][count_j] = round(item_j)
                    results[count_i][count_j] = '$' + str(results[count_i][count_j])
        return results

    @staticmethod
    def calculate_percent_change_function(results):
        for count, item in enumerate(results):
            last_year_result = item[-2]
            this_year_result = item[-1]
            if last_year_result == 0:
                percent_change = 'NA'
            else:
                change = this_year_result - last_year_result
                percent_change = round((change/last_year_result) * 100, 1)
                percent_change = str(percent_change) + '%'
            results[count] += (percent_change, )
        return results

    def calculate_subtotal_function(self, results):
        i = 1
        j = 0
        year_sub_total = 0
        subtotal = [results[0][0], self.sub_total_text]
        for i in range(0, len(results[0][2:])):
            for j in range(0, len(results) - 1):
                print(str(year_sub_total) + '+' + str(results[j][2 + i]))
                year_sub_total = year_sub_total + results[j][2 + i]
            subtotal.append(year_sub_total)
            year_sub_total = 0
        results.append(subtotal)
        return results

    def return_final_sub_part(self):
        query_result = self.execute_sql_str()
        query_result = self.remove_none_from_query_results(query_result)
        list_query_results = []
        for i in query_result:
            list_query_results.append(list(i))
        print(list_query_results)
        if self.has_sub_total:
            list_query_results = self.calculate_subtotal_function(list_query_results)
        if self.calculate_percentage_change:
            list_query_results = self.calculate_percent_change_function(list_query_results)
        if self.round_using_form_masking_class:
            list_query_results = self.round_query_results_function(list_query_results)
        for count, item in enumerate(list_query_results):
            list_query_results[count] = list_query_results[count][1:]
        return list_query_results


