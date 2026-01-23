class DisplayService:
  def __init__(self, display, clock):
    self.display = display
    self.clock = clock

  def updateTime(self):
    time = self.clock.getTime()
    hour = time["hour"]
    minute = time["minute"]

    self.display.setNumber([
      hour // 10,
      hour % 10,
      minute // 10,
      minute % 10
    ])