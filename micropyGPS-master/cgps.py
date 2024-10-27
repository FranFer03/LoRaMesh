from machine import UART
from MicropyGPS import MicropyGPS

class GPS:
    def __init__(self, gps_data):
        self.gps_data = gps_data

    def is_leap_year(self, year):
        if year % 4 == 0:
            if year % 100 == 0:
                return year % 400 == 0
            return True
        return False

    def days_in_year(self, year):
        return 366 if self.is_leap_year(year) else 365

    def days_in_month(self, month, year):
        days_per_month = [31, 29 if self.is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return days_per_month[month - 1]

    def to_unix_timestamp(self):
        day, month, year_offset = self.gps_data.date
        hours, minutes, seconds = self.gps_data.timestamp

        year = 2000 + year_offset
        total_days = 0

        for y in range(1970, year):
            total_days += self.days_in_year(y)

        for m in range(1, month):
            total_days += self.days_in_month(m, year)

        total_days += day - 1

        unix_timestamp = (total_days * 86400) + (hours * 3600) + (minutes * 60) + int(seconds)
        return unix_timestamp
    
    def convert(self, secciones):
        if secciones[0] == 0:
            return None
        data = secciones[0] + (secciones[1] / 60.0)
        if secciones[2] in ('S', 'W'):
            data = -data
        return int(data * 1000000)  # Convert to integer with precision of six decimal places
    
    def location(self):
        latitude = self.gps_data.latitude
        longitude = self.gps_data.longitude
        return self.convert(latitude), self.convert(longitude)

    def give_location(self):
        if self.gps_data.satellite_data_updated() and self.gps_data.satellites_in_use > 3:
            unix_timestamp = self.to_unix_timestamp()
            latitude, longitude = self.location()
            return unix_timestamp, latitude, longitude
        else:
            return 0, 0, 0
