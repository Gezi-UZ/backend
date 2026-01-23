import network
import time


class WifiService:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.wlan.connect(self.ssid, self.password)
            while not self.wlan.isconnected():
                time.sleep(0.5)

        print("WiFi conectado:", self.wlan.ifconfig())
