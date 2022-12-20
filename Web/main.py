# Import required libraries
import network
import socket
from time import sleep
import dht
from machine import Pin

# Pin setup
intled = machine.Pin("LED", machine.Pin.OUT)
sensor = dht.DHT22(Pin(2))

# turn the onboard LED ON to indicate startup
intled.value(1)
# wait for 3 seconds
sleep(3)
# turn the onboard LED OFF
intled.value(0)


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# prevent the wireless chip from
# activating power-saving mode when it is idle
wlan.config(pm = 0xa11140)
# set a static IP address for Pico
# your router IP could be very different eg:
# 192.168.1.1
wlan.ifconfig(('10.0.0.94', '255.255.255.0', '10.0.0.2', '8.8.8.8'))
# enter your wifi "SSID" and "PASSWORD"
wlan.connect("mySSID", "myPASSWORD")


def webpage(temperature, humidity):
    """Creates the HTML to create the web page

    Args:
        temperature (str): Temperature reading from sensor
        humidity (str): Humidity reading from sensor

    Returns:
        str: Some basic HTML to display the server page
    """
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>Pico DHT22</title>
        </head>
        <body>
            <h1>Pico W - DHT22</h1>
            <font size="+2">
            <p>Temperature: {temperature}C</p>
            <p>Humidity: {humidity}%</p>
            </font>
        </body>
        </html>
        """
    return str(html)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    sleep(1)

# Handle connection error
if wlan.status() != 3:
    intled.value(0)
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print('listening on', addr)

# Listen for connections
# Search for up to 10 seconds for network connection
while True:
    if wlan.status() == 3:
        intled.value(1)
    else:
        intled.value(0)
    try:
        #Get the measurements from the sensor
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        print(f"Temperature: {temperature}°C   Humidity: {humidity}% ")
        
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        request = str(request)
        print(request)

        # display the webpage for the customer
        html = webpage(temperature, humidity)
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(html)
        cl.close()
        
    except OSError as e:
        cl.close()
        print('connection closed')
