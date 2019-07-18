#####
# Utility functions
#####

#
def monthdelta(date, delta):
    """
    function to calculate date - delta months
    :param date: a datetime.date object
    :param delta: an int representing the number of months
    :return: a new datetime.date object
    """
    delta = -int(delta)
    m, y = (date.month + delta) % 12, date.year + (date.month + delta - 1) // 12
    if not m: m = 12
    d = min(date.day, [31,
                       29 if y % 4 == 0 and not y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][
        m - 1])
    return date.replace(day=d, month=m, year=y)


#
def get_wsdot_color(i, hex_or_rgb="hex", alpha=99):
    """
    function to generate and incremented WSDOT color scheme primarily for charts.  If alpha is provided it will return a hex color with an alpha component
    :param i: int
    :param alpha: int
    :param hex_or_rgb: str either 'hex' or 'rgb' selects the output format
    :return: a string representing a WSDOT hex color
    """
    j = i % 8
    if hex_or_rgb == 'hex':
        wsdot_colors = ["#2C8470",
                        "#97d700",
                        "#00aec7",
                        "#5F615E",
                        "#00b140",
                        "#007fa3",
                        "#ABC785",
                        "#593160"]
        color = wsdot_colors[j]
        # HEX with alpha is not compatible with chart js.

    elif hex_or_rgb == 'rgb':
        if alpha == 100:
            alpha = 99
        wsdot_colors = ["rgba(44,132,112,0.{})".format(alpha),
                        "rgba(151,215,0,0.{})".format(alpha),
                        "rgba(0,174,199,0.{})".format(alpha),
                        "rgba(95,97,94,0.{})".format(alpha),
                        "rgba(0,177,64,0.{})".format(alpha),
                        "rgba(0,127,163,0.{})".format(alpha),
                        "rgba(171,199,133,0.{})".format(alpha),
                        "rgba(89,49,96,0.{})".format(alpha)]
        color = wsdot_colors[j]
    print(color)
    return color

def calculate_biennium(date):
    import datetime

    if not isinstance(date, datetime.date):
        raise TypeError("date must be a datetime.date object")

    def biennium_str(first_year):
        return str(first_year)[-2:]+ "-" + str(first_year + 2)[-2:]

    reference_biennium_start_year = 2017
    if (date.year - reference_biennium_start_year) % 2 == 0:
        start_year = reference_biennium_start_year + (date.year - reference_biennium_start_year)
        if date > datetime.date(start_year, 6, 1):
            return biennium_str(start_year)
        else:
            return biennium_str(start_year - 2)
    else:
        start_year = reference_biennium_start_year + (date.year - reference_biennium_start_year) - 1
        return biennium_str(start_year)

def green_house_gas_per_vanpool_mile():
    """
    Function returns a multiplier to be multiplied with a number of miles traveled by vanpool to yield total CO2 equivalents emited
    :return: vanpool emissions factor
    """
    percent_small_van = 0.60  # update using report found here:G:\Evaluation Group\RVCT and WSRO Vanpool\Info For Greenhouse Gas Calculations\VanpoolSeatingCapcityReport.xlsx (right click on the pivot table and hit refresh to get latest data)
    small_van_mpg = 24.00  # Small Vans are vans with a wheelbase less than 121 inches.  Some but not all 8 passanger vanpool vans have a wheelbase less than 21 inches.  Use the percent of vanpool vans with a passanger capacity of 8 or less.
    large_van_mpg = 17.40
    co2e_per_gallon = 0.008887  # units = metric tones

    fleet_fuel_efficiency = (small_van_mpg * percent_small_van) + (large_van_mpg * (1 - percent_small_van))
    co2_per_vanpool_mile_traveled = (1 / fleet_fuel_efficiency) * co2e_per_gallon

    return co2_per_vanpool_mile_traveled

def green_house_gas_per_sov_mile():
    """
    Function returns a multiplier to be multiplied with a number of miles traveled by vanpool to yield total CO2 equivalents emited
    :return: vanpool emissions factor
    """

    sov_miles_per_gallon = 22
    co2e_per_gallon = 0.008887  # units = metric tones

    co2_per_sov_mile_traveled = (1 / sov_miles_per_gallon) * co2e_per_gallon

    return co2_per_sov_mile_traveled

