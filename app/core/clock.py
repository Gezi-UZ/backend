from machine import RTC


class Clock: 
  def __init__(self):
    self.rtc = RTC()

  def setTime(self, year, month, day, hour, minute, second):
    self.rtc.datetime((year, month, day, 0, hour, minute, second, 0))

  def getTime(self):
    dt = self.rtc.datetime()
    return {
      "year": dt[0],
      "month": dt[1],
      "day": dt[2],
      "hour": dt[4],
      "minute": dt[5],
      "second": dt[6],
    }