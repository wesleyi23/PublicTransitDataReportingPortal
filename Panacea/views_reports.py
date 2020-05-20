#####
# This file contains the views needed to generate pdf reports from html, using WeasyPrint
#####
from weasyprint import HTML
from django.shortcuts import render

from Panacea.utilities import find_user_organization
from .models import cover_sheet, tax_rates


def cover_sheet_report(request, pdf=None):
    user_org = find_user_organization(request.user.id)
    org_cover_sheet = cover_sheet.objects.get(organization_id=user_org.id)
    agency_type = user_org.summary_organization_classifications
    if agency_type != "Community provider" and agency_type != "Medicaid broker":
        tax_description, created = tax_rates.objects.get_or_create(organization_id=user_org.id)
        tax_description = tax_description.tax_rate_description
    if pdf == 'pdf':
        HTML('./templates/reports/cover_sheet.html').write_pdf('test.pdf')
    else:
        return render(request, '../templates/reports/cover_sheet.html', {'cover_sheet': org_cover_sheet,
                                                                         'agency_type': agency_type,
                                                                         'organization': user_org,
                                                                         'tax_description': tax_description})

