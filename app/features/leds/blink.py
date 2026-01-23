from machine import Pin
from utime import sleep

led_red = Pin(5, Pin.OUT)
led_green = Pin(4, Pin.OUT)
led_blue = Pin(2, Pin.OUT)

print("LED starts flashing...")
while True:
    try:
        led_red.on()
        sleep(1) # sleep 1sec
        led_red.off()
        sleep(1)
        led_green.on()
        sleep(1)
        led_green.off()
        sleep(1)
        led_blue.on()
        sleep(1)
        led_blue.off()
        sleep(1)

        led_red.toggle()
        led_green.toggle()
        led_blue.toggle()
        sleep(3)
    except KeyboardInterrupt:
        break
led_green.off()
print("Finished.")
