import django
django.setup()
from Panacea.models import organization


Org = organization(name="WSDOT",
                   address_line_1="Test address line 1",
                   address_line_2="Test address line 2",
                   city="Test City",
                   zip_code="98504"
                   )
Org.save()

Org = organization(name="Data Submitter 1",
                   address_line_1="Test address line 1",
                   address_line_2="Test address line 2",
                   city="Test City",
                   zip_code="98504"
                   )
Org.save()

Org = organization(name="Data Submitter 2",
                   address_line_1="Test address line 1",
                   address_line_2="Test address line 2",
                   city="Test City",
                   zip_code="98504"
                   )
Org.save()