#####
# This file contains the views needed to generate pdf reports from html, using WeasyPrint
#####
from weasyprint import HTML


def cover_sheet_report():
    HTML('./templates/reports/cover_sheet.html').write_pdf('test.pdf')

