import time
from machine import RTC

def is_leap_year(year):
    return (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))

def days_in_month(month, year):
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and is_leap_year(year):
        return 29
    return days_per_month[month - 1]

def calculate_days_since_epoch(year, month, day, hour, minute, second):
    """ Calcula los días transcurridos desde 1970-01-01 hasta la fecha dada """
    days = (year - 1970) * 365 + (year - 1969) // 4 
    for m in range(1, month):
        days += days_in_month(m, year)
    days += day - 1
    total_seconds = days * 86400
    total_seconds += hour * 3600 + minute * 60 + second
    
    return total_seconds


rtc = RTC()
rtc.datetime((2024, 11, 27, 2, 10, 30, 0, 0))
rtc_time = rtc.datetime()


year, month, day, hour, minute, second = rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[3], rtc_time[4], rtc_time[5]
timestamp = calculate_days_since_epoch(year, month, day, hour, minute, second)
print(f"Timestamp calculado manualmente: {timestamp}")
