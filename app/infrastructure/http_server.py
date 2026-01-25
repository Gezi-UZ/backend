import socket
import json
import _thread


class HttpServer:
    def __init__(self, led_controller, clock):
        self.led_controller = led_controller
        self.clock = clock
        self.running = True

    def _parse_request(self, request):
        """Parse HTTP request and return method, path, and body"""
        lines = request.split("\r\n")
        if len(lines) < 1:
            return None, None, {}
        
        parts = lines[0].split(" ")
        if len(parts) < 3:
            return None, None, {}
        
        method, path, _ = parts

        body = {}
        if "\r\n\r\n" in request:
            try:
                body_str = request.split("\r\n\r\n")[1].strip()
                if body_str:
                    body = json.loads(body_str)
            except:
                body = {}

        return method, path, body

    def _response(self, connection, status_code, status_text, payload):
        """Send HTTP response with CORS headers"""
        response_body = json.dumps(payload)
        response = (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
            + response_body
        )
        connection.send(response.encode())

    def _handle_led_post(self, body):
        """Handle POST /led request"""
        led_id = body.get("id")
        state = body.get("state")

        if not led_id or state is None:
            return 400, "Bad Request", {"success": False, "error": "Missing 'id' or 'state' field"}

        if not isinstance(state, bool):
            return 400, "Bad Request", {"success": False, "error": "'state' must be boolean"}

        ok = self.led_controller.setLed(led_id, state)
        if not ok:
            return 404, "Not Found", {"success": False, "error": f"LED '{led_id}' not found"}

        return 200, "OK", {"success": True, "data": {"id": led_id, "state": state}}

    def _handle_led_get(self, path):
        """Handle GET /led or GET /led/{id} request"""
        if path == "/led":
            # GET /led - return all LED states
            leds = self.led_controller.getAllLeds()
            return 200, "OK", {"success": True, "data": leds}
        elif path.startswith("/led/"):
            # GET /led/{id} - return single LED state
            led_id = path.split("/")[-1]
            led_state = self.led_controller.getLed(led_id)
            if led_state is None:
                return 404, "Not Found", {"success": False, "error": f"LED '{led_id}' not found"}
            return 200, "OK", {"success": True, "data": led_state}
        
        return 404, "Not Found", {"success": False, "error": "Invalid LED path"}

    def _handle_time_post(self, body):
        """Handle POST /time request"""
        hour = body.get("hour")
        minute = body.get("minute")

        if hour is None or minute is None:
            return 400, "Bad Request", {"success": False, "error": "Missing 'hour' or 'minute' field"}

        if not isinstance(hour, int) or not isinstance(minute, int):
            return 400, "Bad Request", {"success": False, "error": "'hour' and 'minute' must be integers"}

        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            return 400, "Bad Request", {"success": False, "error": "Invalid time: hour must be 0-23, minute must be 0-59"}

        self.clock.setTime(hour, minute)
        return 200, "OK", {"success": True, "data": {"hour": hour, "minute": minute}}

    def _handle_time_get(self):
        """Handle GET /time request"""
        time_data = self.clock.getTime()
        return 200, "OK", {"success": True, "data": time_data}

    def _handle_health(self):
        """Handle GET /health request"""
        return 200, "OK", {"success": True, "data": {"status": "healthy"}}

    def _handle_client(self, connection, address):
        """Handle individual client connection in a separate thread"""
        try:
            request = connection.recv(1024).decode()
            
            if not request:
                return

            method, path, body = self._parse_request(request)

            if method is None or path is None:
                self._response(connection, 400, "Bad Request", {"success": False, "error": "Invalid request"})
                return

            # Route handling
            if method == "POST" and path == "/led":
                status, text, payload = self._handle_led_post(body)
                self._response(connection, status, text, payload)

            elif method == "GET" and (path == "/led" or path.startswith("/led/")):
                status, text, payload = self._handle_led_get(path)
                self._response(connection, status, text, payload)

            elif method == "POST" and path == "/time":
                status, text, payload = self._handle_time_post(body)
                self._response(connection, status, text, payload)

            elif method == "GET" and path == "/time":
                status, text, payload = self._handle_time_get()
                self._response(connection, status, text, payload)

            elif method == "GET" and path == "/health":
                status, text, payload = self._handle_health()
                self._response(connection, status, text, payload)

            elif method == "OPTIONS":
                # Handle CORS preflight requests
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                    "Access-Control-Allow-Headers: Content-Type\r\n"
                    "Content-Length: 0\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                connection.send(response.encode())

            else:
                self._response(connection, 404, "Not Found", {"success": False, "error": "Route not found"})

        except Exception as e:
            try:
                self._response(connection, 500, "Internal Server Error", {"success": False, "error": "Internal server error"})
            except:
                pass
        finally:
            connection.close()

    def start(self):
        """Start the HTTP server with threaded request handling"""
        address = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(address)
        server_socket.listen(5)

        print("HTTP Server ativo na porta 80")
        print("Endpoints disponiveis:")
        print("  GET  /led           - Le todos os LEDs")
        print("  GET  /led/{id}      - Le um LED especifico")
        print("  POST /led           - Controla LED (body: {id, state})")
        print("  GET  /time          - Le hora atual")
        print("  POST /time          - Define hora (body: {hour, minute})")
        print("  GET  /health        - Status do servidor")

        try:
            while self.running:
                connection, address = server_socket.accept()
                # Handle each connection in a separate thread
                _thread.start_new_thread(
                    self._handle_client,
                    (connection, address)
                )
        except KeyboardInterrupt:
            print("Servidor interrompido")
        finally:
            server_socket.close()
