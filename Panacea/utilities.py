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
def get_wsdot_color(i):
    """
    function to generate and incremented WSDOT color scheme primarily for charts
    :param i: int
    :return: a string representing a WSDOT hex color
    """
    wsdot_colors = ["#2C8470",
                    "#97d700",
                    "#00aec7",
                    "#5F615E",
                    "#00b140",
                    "#007fa3",
                    "#ABC785",
                    "#593160"]
    j = i % 8
    return wsdot_colors[j]

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

