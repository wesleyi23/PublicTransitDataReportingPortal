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


