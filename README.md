# Gezi - IoT

A MicroPython-based IoT project for ESP32 that provides remote LED control and digital clock display via HTTP API and Flutter mobile app.

## Overview

Ciyera is an embedded system that runs on an ESP32 microcontroller and offers:

- Remote RGB LED control over HTTP API
- 4-digit 7-segment display showing current time
- WiFi connectivity for network communication
- Real-Time Clock (RTC) integration for accurate timekeeping
- Flutter mobile app support for user-friendly control
- Concurrent request handling for responsive performance

## Hardware Requirements

- ESP32 Microcontroller (or compatible MicroPython-enabled board)
- 3x RGB LEDs (or individual LEDs)
  - Red LED: GPIO 5
  - Green LED: GPIO 4
  - Blue LED: GPIO 2
- 4-digit 7-segment Display
  - Digit select pins: GPIO 18, 19, 21, 22
  - Segment pins: GPIO 13, 14, 27, 26, 25, 33, 32 (a-g)
- Real-Time Clock (RTC) module (built-in RTC available on ESP32)
- WiFi connectivity (built-in on ESP32)
- USB cable for programming and power

## Project Structure

```
Ciyera/
├── boot.py                          # Initialization script (runs on startup)
├── main.py                          # Application entry point
├── README.md                        # This file
├── app/
│   ├── core/
│   │   ├── clock.py                # RTC clock interface
│   │   └── config.py               # Configuration settings
│   ├── features/
│   │   ├── clock/
│   │   │   ├── clock_routes.py     # Clock API routes
│   │   │   └── clock_service.py    # Clock business logic
│   │   ├── leds/
│   │   │   ├── blink.py            # LED blink test utility
│   │   │   ├── led_controller.py   # LED control logic
│   │   │   └── led_routes.py       # LED API routes
│   │   └── display/
│   │       ├── display_service.py  # Display update logic
│   │       └── seven_segment.py    # 7-segment display driver
│   └── infrastructure/
│       ├── http_server.py          # HTTP server with routing
│       └── wifi.py                 # WiFi connection service
```

## Installation

### 1. Flash MicroPython

Follow the official MicroPython documentation to flash your ESP32 with MicroPython firmware.

### 2. Clone Repository

```bash
git clone <repository-url>
cd Ciyera
```

### 3. Upload Files to ESP32

Use a MicroPython IDE (e.g., Thonny, VS Code with PyMUP) to upload all files to the ESP32:

- `boot.py` - Optional initialization
- `main.py` - Main application
- `app/` directory - All application modules

### 4. Configure WiFi Credentials

Edit `main.py` and update WiFi credentials:

```python
wifi = WifiService("YOUR_SSID", "YOUR_PASSWORD")
```

### 5. Power On

Connect the ESP32 to power. The device will:
1. Connect to WiFi
2. Initialize LEDs and display
3. Start the HTTP server on port 80
4. Display available endpoints in serial output

## API Endpoints

All responses are in JSON format with consistent structure:

```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

### LED Control

#### Get All LED States
```
GET /led

Response:
{
  "success": true,
  "data": {
    "led_red": true,
    "led_green": false,
    "led_blue": true
  }
}
```

#### Get Single LED State
```
GET /led/{id}

Example: GET /led/led_red

Response:
{
  "success": true,
  "data": {
    "id": "led_red",
    "state": true
  }
}
```

#### Control LED
```
POST /led

Request Body:
{
  "id": "led_red",
  "state": true
}

Response:
{
  "success": true,
  "data": {
    "id": "led_red",
    "state": true
  }
}
```

**LED IDs:** `led_red`, `led_green`, `led_blue`

**State:** `true` (on) or `false` (off)

### Clock / Time Control

#### Get Current Time
```
GET /time

Response:
{
  "success": true,
  "data": {
    "year": 2026,
    "month": 1,
    "day": 23,
    "hour": 14,
    "minute": 30,
    "second": 45
  }
}
```

#### Set Time
```
POST /time

Request Body:
{
  "hour": 14,
  "minute": 30
}

Response:
{
  "success": true,
  "data": {
    "hour": 14,
    "minute": 30
  }
}
```

**Parameters:**
- `hour`: 0-23 (required)
- `minute`: 0-59 (required)

### Server Health

#### Health Check
```
GET /health

Response:
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

### 400 Bad Request
```json
{
  "success": false,
  "error": "Missing 'id' or 'state' field"
}
```

Causes:
- Missing required fields
- Invalid data types
- Out-of-range values

### 404 Not Found
```json
{
  "success": false,
  "error": "LED 'led_invalid' not found"
}
```

Causes:
- Invalid LED ID
- Invalid route path

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error"
}
```

Causes:
- Unexpected server errors (details not exposed for security)

## Flutter Integration

The API is designed for easy integration with Flutter mobile applications:

### CORS Support
- Cross-Origin Resource Sharing (CORS) headers enabled
- Supports preflight OPTIONS requests
- Compatible with web-based clients

### HTTP Methods
- GET - Retrieve data
- POST - Send commands
- OPTIONS - CORS preflight

### Content-Type
- All requests and responses use `application/json`
- Automatic JSON encoding/decoding

### Example Flutter Request

```dart
import 'package:http/http.dart' as http;

// Turn on red LED
Future<void> turnOnLed(String ipAddress) async {
  final response = await http.post(
    Uri.parse('http://$ipAddress/led'),
    headers: {'Content-Type': 'application/json'},
    body: json.encode({
      'id': 'led_red',
      'state': true,
    }),
  );

  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    print('LED turned on: ${data['data']}');
  } else {
    print('Error: ${response.statusCode}');
  }
}

// Get current time
Future<void> getCurrentTime(String ipAddress) async {
  final response = await http.get(
    Uri.parse('http://$ipAddress/time'),
  );

  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    print('Current time: ${data['data']['hour']}:${data['data']['minute']}');
  }
}
```

## Architecture

### Core Components

**WiFi Service** (`app/infrastructure/wifi.py`)
- Handles WiFi connection and reconnection
- Stores network credentials
- Provides connection status

**HTTP Server** (`app/infrastructure/http_server.py`)
- Handles all incoming HTTP requests
- Routes requests to appropriate handlers
- Supports concurrent client connections via threading
- Implements request validation and error handling
- Adds CORS headers for cross-origin requests

**LED Controller** (`app/features/leds/led_controller.py`)
- Manages GPIO pins for LEDs
- Provides methods to control LED state
- Maintains current LED state information
- Returns boolean values for state queries

**Clock** (`app/core/clock.py`)
- Interfaces with ESP32's RTC module
- Reads and sets system time
- Returns time in dictionary format

**Display Service** (`app/features/display/display_service.py`)
- Updates 7-segment display with current time
- Coordinates with Clock service
- Manages digit-to-segment mapping

**7-Segment Display** (`app/features/display/seven_segment.py`)
- Controls 4-digit display hardware
- Uses multiplexing for efficient GPIO usage
- Timer-based refresh mechanism

## Request Flow

1. Client sends HTTP request to server
2. HTTP Server parses request (method, path, body)
3. Request validation checks for required fields and data types
4. Route handler processes the request
5. Business logic executes (LED control, time query, etc.)
6. Response is formatted with status, data, and optional error message
7. HTTP response is sent with appropriate status code and headers
8. Connection is closed

## Development Guide

### Adding New Endpoints

1. Create handler method in `HttpServer._handle_<feature>_<method>()`
2. Add route matching logic in `HttpServer._handle_client()`
3. Return `(status_code, status_text, payload)` tuple
4. Implement input validation in handler method

Example:

```python
def _handle_custom_post(self, body):
    # Validate input
    param = body.get("param")
    if not param:
        return 400, "Bad Request", {"success": False, "error": "Missing 'param'"}
    
    # Process request
    result = do_something(param)
    
    # Return response
    return 200, "OK", {"success": True, "data": result}
```

### Debugging

1. Use MicroPython REPL to test individual components
2. Check serial output for WiFi and server status messages
3. Use HTTP client tools (curl, Postman) to test API endpoints
4. Monitor request/response in server logs

### Performance Considerations

- Thread pool size limited to prevent resource exhaustion
- Request timeout not implemented (add if needed)
- Maximum request body size: 1024 bytes
- LED operations are non-blocking
- Display refresh rate: 800 Hz (multiplexing)

## Troubleshooting

### WiFi Connection Issues
- Verify SSID and password are correct
- Check that 2.4 GHz WiFi is available (not 5 GHz)
- Review serial output for connection errors
- Ensure ESP32 is within WiFi range

### Server Not Starting
- Verify port 80 is not already in use
- Check for GPIO conflicts with other devices
- Review serial output for error messages
- Ensure all files are uploaded correctly

### LED Not Responding
- Verify GPIO pin connections are correct
- Test with blink.py script
- Check LED polarity (anode/cathode)
- Verify LED controller method names match HTTP server calls

### Display Not Updating
- Verify GPIO pin assignments match seven_segment.py
- Test display refresh rate
- Check for GPIO conflicts
- Ensure clock service is providing correct time

### API Request Failures
- Verify correct endpoint path
- Check request body JSON format
- Ensure correct HTTP method (GET vs POST)
- Review error message for validation issues
- Verify server is running (check /health endpoint)

## Features

- Multi-threaded HTTP server for concurrent client connections
- Input validation with descriptive error messages
- CORS support for cross-origin requests
- Proper HTTP status codes for different error types
- Real-time LED control with state querying
- Accurate time keeping with RTC integration
- 4-digit display for visual feedback
- Clean separation of concerns (core, features, infrastructure)
- Consistent JSON API response format

## Future Enhancements

- LED color control (RGB mixing)
- LED animation patterns
- Time synchronization via NTP
- Temperature sensor integration
- Data logging and statistics
- Authentication/API key support
- Alarm functionality
- Schedule-based LED control
- Web dashboard UI
- OTA firmware updates

## License

MIT License - Feel free to modify and distribute.

## Author

Ciyera IoT Project

## Support

For issues, questions, or contributions, please refer to the project repository.
