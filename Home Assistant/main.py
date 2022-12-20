# Import required libraries
import network
import socket
from time import sleep
import dht
from machine import Pin
import json

# Pin setup
intled = machine.Pin("LED", machine.Pin.OUT)
sensor = dht.DHT22(Pin(2))

# Indicate that the app started
intled.value(1)
sleep(3)
intled.value(0)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# prevent the wireless chip from activating power-saving mode when it is idle
wlan.config(pm = 0xa11140) 
# sets a static ip for this Pico 
wlan.ifconfig(('10.0.0.94', '255.255.255.0', '10.0.0.2', '8.8.8.8')) 
# Connect to your AP using your login details
wlan.connect("mySSID", "myPASSWORD") 

# Search for up to 10 seconds for network connection
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    intled.value(1)
    print('waiting for connection...')
    sleep(1)

# Raise an error if Pico is unable to connect
if wlan.status() != 3:
    intled.value(0)
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

# Open a socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

# Display your IP address
print('listening on', addr)

# Listen for connections
while True:
    # If pico is connected to wifi put the onboard LED on else off
    if wlan.status() == 3: 
        intled.value(1)
    else:
        intled.value(0)
        
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        request = str(request)
        print(request)
        
        # Get the data from the DHT22 sensor
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        print(f"Temperature: {temperature}°C   Humidity: {humidity}% ")
        

        # prep the data to send to Home Assistant as type Json
        data = { "hum": humidity, "temp": temperature }
        JsonData = json.dumps(data)
        
        # Send headers notifying the receiver that the data is of type Json for application consumption 
        cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        # Send the Json data
        cl.send(JsonData)
        # Close the connection
        cl.close()


    except OSError as e:
        cl.close()
        print('connection closed')
