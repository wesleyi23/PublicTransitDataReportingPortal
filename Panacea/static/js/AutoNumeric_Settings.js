$(document).ready(function() {
    int_format = new AutoNumeric.multiple('.AutoNumeric-Int input', {
        "dotDecimalCharCommaSeparator": true,
        "unformatOnSubmit": true,
        "decimalPlaces": 0,
    });
    float_format = new AutoNumeric.multiple('.AutoNumeric-Float input', {
        "dotDecimalCharCommaSeparator": true,
        "unformatOnSubmit": true,
    });
    money_format = new AutoNumeric.multiple('.AutoNumeric-Money input', {
        "dotDecimalCharCommaSeparator": true,
        "unformatOnSubmit": true,
        "currencySymbol": '$',
        "decimalPlaces": 0,
    });
})