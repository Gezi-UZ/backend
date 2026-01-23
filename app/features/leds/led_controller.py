from machine import Pin


class LedController:
    def __init__(self):
        self.leds = {
            "led_red": Pin(5, Pin.OUT),
            "led_green": Pin(4, Pin.OUT),
            "led_blue": Pin(2, Pin.OUT),
        }

    def setLed(self, led_id, state):
        if led_id in self.leds:
            self.leds[led_id].value(1 if state else 0)
            return True
        return False

    def getLed(self, led_id):
        """Get the current state of a specific LED"""
        if led_id in self.leds:
            return {"id": led_id, "state": bool(self.leds[led_id].value())}
        return None

    def getAllLeds(self):
        """Get the current state of all LEDs"""
        return {
            led_id: bool(self.leds[led_id].value())
            for led_id in self.leds
        }
