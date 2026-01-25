try:
    print("=== Ciyera IoT System Starting ===")
    
    # Import modules
    print("Importing modules...")
    from app.infrastructure.wifi import WifiService
    from app.infrastructure.http_server import HttpServer
    from app.features.leds.led_controller import LedController
    from app.core.clock import Clock
    from app.features.display.seven_segment import SevenSegment
    from app.features.display.display_service import DisplayService
    
    # WiFi Connection
    print("Initializing WiFi...")
    wifi = WifiService("Wen's S20+", "02sept1945")
    wifi.connect()
    print("WiFi connected!")
    
    # Initialize components
    print("Initializing components...")
    led_controller = LedController()
    print("LED Controller initialized")
    
    clock = Clock()
    print("Clock initialized")
    
    # Initialize display
    try:
        display = SevenSegment()
        display_service = DisplayService(display, clock)
        print("Display initialized")
    except Exception as e:
        print(f"Display initialization warning: {e}")
    
    # Start HTTP Server
    print("Starting HTTP Server...")
    server = HttpServer(led_controller, clock)
    server.start()

except Exception as e:
    print(f"FATAL ERROR: {e}")
