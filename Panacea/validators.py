from django import forms


def validate_image_file(file):
    ALLOWED_EXTENSIONS = [".png", ".jpeg", ".jpg", ".tif"]

    valid_ext = False

    for ext in ALLOWED_EXTENSIONS:
        if ext in file.name.lower():
            valid_ext = True

    if not valid_ext:
        raise forms.ValidationError('File type not supported.')


