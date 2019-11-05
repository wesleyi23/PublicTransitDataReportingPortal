$(document).ready(function() {
    int_format = new AutoNumeric.multiple('.AutoNumeric-Int input.AutoNumeric-On', {
        "dotDecimalCharCommaSeparator": true,
        "unformatOnSubmit": true,
        "decimalPlaces": 0,
    });
    float_format = new AutoNumeric.multiple('.AutoNumeric-Float input.AutoNumeric-On', {
        "dotDecimalCharCommaSeparator": true,
        "unformatOnSubmit": true,
    });
    money_format = new AutoNumeric.multiple('.AutoNumeric-Money input.AutoNumeric-On', {
        "dotDecimalCharCommaSeparator": true,
        "unformatOnSubmit": true,
        "currencySymbol": '$',
        "decimalPlaces": 0,
    });
})