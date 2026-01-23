from machine import Pin, Timer


class SevenSegment:
    DIGITS_MAP = {
        0: [1, 1, 1, 1, 1, 1, 0],
        1: [0, 1, 1, 0, 0, 0, 0],
        2: [1, 1, 0, 1, 1, 0, 1],
        3: [1, 1, 1, 1, 0, 0, 1],
        4: [0, 1, 1, 0, 0, 1, 1],
        5: [1, 0, 1, 1, 0, 1, 1],
        6: [1, 0, 1, 1, 1, 1, 1],
        7: [1, 1, 1, 0, 0, 0, 0],
        8: [1, 1, 1, 1, 1, 1, 1],
        9: [1, 1, 1, 1, 0, 1, 1],
    }

    def __init__(self):
        self.digits = [
            Pin(18, Pin.OUT),
            Pin(19, Pin.OUT),
            Pin(21, Pin.OUT),
            Pin(22, Pin.OUT)
        ]

        self.segments = [
            Pin(13, Pin.OUT), # a
            Pin(14, Pin.OUT), # b
            Pin(27, Pin.OUT), # c
            Pin(26, Pin.OUT), # d
            Pin(25, Pin.OUT), # e
            Pin(33, Pin.OUT), # f
            Pin(32, Pin.OUT), # g
        ]

        self.current_digits = [0, 0, 0, 0]
        self.index = 0 
        self.timer = Timer(0)
        self.timer.init(freq = 800, mode = Timer.PERIODIC, callback = self._refresh)
        self.enabled = True

    def setNumber(self, numbers):
        self.current_digits = numbers

    def _refresh(self, t):
        for digits in self.digits:
            digits.value(0)

        value = self.current_digits[self.index]
        pattern = self.DIGITS_MAP[value]

        for segment, state in zip(self.segments, pattern):
            segment.value(0 if state else 1) # common cathode

        self.digits[self.index].value(1)
        self.index = (self.index + 1) % 4
        
        if not self.enabled:
            for digit in self.digits:
                digits.value(0)
            return

    def power(self, state: bool):
        self.enabled = state