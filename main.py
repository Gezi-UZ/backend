from app.infrastructure.wifi import WifiService
from app.infrastructure.http_server import HttpServer
from app.features.leds.led_controller import LedController
from app.core.clock import Clock
from app.features.display.seven_segment import SevenSegment
from app.features.display.display_service import DisplayService

wifi = WifiService("Wen's S20+", "02sept1945")
wifi.connect()

led_controller = LedController()
clock = Clock()

server = HttpServer(led_controller, clock)
server.start()

display = SevenSegment()
display_service = DisplayService(display, clock)
