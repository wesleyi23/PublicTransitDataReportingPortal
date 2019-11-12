from django import forms


def exceeds_limits(data1, data2, category):

    if abs((data2-data1)/data1) >= .15:
        raise forms.ValidationError('Change between the previous year and this year has exceeded 15%. Please provide a comment')

def revenue_is_larger_than_total(data1, data2, category1, category2):
    if data1 > data2:
        raise forms.ValidationError(('Please amend the following {} as it exceeds the total listed in this {}').format(category1, category2))


def validate_image_file(file):
    ALLOWED_EXTENSIONS = [".png", ".jpeg", ".jpg", ".tif"]

    valid_ext = False

    for ext in ALLOWED_EXTENSIONS:
        if ext in file.name.lower():
            valid_ext = True

    if not valid_ext:
        raise forms.ValidationError('File type not supported.')


