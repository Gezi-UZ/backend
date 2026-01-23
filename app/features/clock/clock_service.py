class ClockService:
    def __init__(self):
        self.hour = 0
        self.minute = 0

    def setTime(self, hour, minute):
        self.hour = hour
        self.minute = minute

    def getTime(self):
        return {"hour": self.hour, "minute": self.minute}
