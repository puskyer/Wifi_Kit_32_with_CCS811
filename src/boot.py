# This file is executed on every boot (including wake-boot from deepsleep)

import esp, uos, machine, gc, ssd1306, utime
from umqttsimple import MQTTClient
import ubinascii
import micropython
import network

#uos.dupterm(None, 1) # disable REPL on UART(0)
esp.osdebug(None)
gc.collect()

oledIsConnected = False
addrOled = 60
SSD1306_Pin = 16      #oled_rst
Pin_high = 1
Pin_low = 0
i2c_scl = 15
i2c_sda = 4
oled_topofScreen = 0
oled_topofScreenOffset = 0
oled_leftofscreen = 0
oled_leftofscreenOffset = 0
APIsEnabled = False
utelnetserverIsEnabled = False

DataJson = {
  "APSSID" : "ssid",
  "APpassword" : "ssid_password",
  "STSSID" : "ssid",
  "STpassword" : "ssid_password",
  "mqtt_user" : "User",
  "mqtt_password" : "Pass"  
}    

# config.json data file
#{
#"wifi": {
#"APSSID": "<AP>",
#"APpassword": "<pass>",
#"STSSID": "<AP>",
#"STpassword": "<pass>"
#}
#}

#Setup pins for SSD1306 Pin 16 is oled_rst
pin16 = machine.Pin(SSD1306_Pin, machine.Pin.OUT)
pin16.value(Pin_high)

#setup i2c pins 15 scl & 4  sda
i2c = machine.I2C(scl=machine.Pin(i2c_scl),sda=machine.Pin(i2c_sda))

# Scan i2c bus and check if OLDE display are connected
print('Scan i2c bus...')
devices = i2c.scan()
if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))
  for device in devices: 
    if device == addrOled:
      oledIsConnected = True  
    print(device)

if oledIsConnected:
  #setup i2c for ssd1306
  oled = ssd1306.SSD1306_I2C(128,64,i2c)
  print('OLED is now setup')
  #clear screen
  oled.fill(0)
  oled.text('ESP32 Wifi Kit',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled.show()
  oled_topofScreenOffset = oled_topofScreen + 10

import ujson
with open('config.json') as data_file:
   DataJson = ujson.load(data_file)
data_file.close

if APIsEnabled:
   print('Start AP network ')
   client_id = ubinascii.hexlify(machine.unique_id())
   ESPAP = DataJson["wifi"]["APSSID"]+str(client_id[-2])+str(client_id[-1])
   print('SSID = '+str(ESPAP))
   if oledIsConnected:
     oled.text('Start AP network ',oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled_topofScreenOffset = oled_topofScreenOffset + 10
     oled.text('essid is'+str(ESPAP),oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled.show()

   network.phy_mode(network.MODE_11N)
   ap = network.WLAN(network.AP_IF)  # create AP Interface
   ap.active(True)                   # activate AP
   # Set ESSID for AP
   # set authmode to WPA2-PSK
   ap.config(essid=ESPAP, authmode=network.AUTH_WPA2_PSK,password=DataJson["wifi"]["APpassword"])
   ap.config(max_clients=5)          # set max clients to 5
   apconfig = ap.ifconfig()
   print('network config:', apconfig)

   if oledIsConnected:
     #clear screen
     oled.fill(0)
     oled_topofScreenOffset = oled_topofScreen
     oled.text('AP config:',oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled_topofScreenOffset = oled_topofScreenOffset + 10
     oled.text('IP '+str(apconfig[0]),oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled_topofScreenOffset = oled_topofScreenOffset + 10
     oled.text('   '+str(apconfig[1]),oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled_topofScreenOffset = oled_topofScreenOffset + 10
     oled.text('Gw '+str(apconfig[2]),oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled_topofScreenOffset = oled_topofScreenOffset + 10
     oled.text('DNS '+str(apconfig[3]),oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled.show()
     utime.sleep(5)

network.phy_mode(network.MODE_11N)
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(str(DataJson["wifi"]["STSSID"]), str(DataJson["wifi"]["STpassword"]))
print('Start LAN connection')
print('essid is '+DataJson["wifi"]["STSSID"])

if oledIsConnected:
  #clear screen
  oled.fill(0)
  oled_topofScreenOffset = oled_topofScreen
  oled.text('Start LAN connection',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('essid is '+DataJson["wifi"]["STSSID"] ,oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled.show()

while station.isconnected() == False:
    #pass
    utime.sleep_ms(500)
    print('Connecting')
print('Connection successful')
lanconfig=station.ifconfig()
print(lanconfig)

if oledIsConnected:
  #clear screen
  oled.fill(0)
  oled_topofScreenOffset = oled_topofScreen
  oled.text('LAN config:',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('IP '+str(lanconfig[0]),oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('   '+str(lanconfig[1]),oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('Gw '+str(lanconfig[2]),oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('DNS '+str(lanconfig[3]),oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled.show()
  utime.sleep(10)

from ntptime import settime
settime()


if oledIsConnected:
  #clear screen
  oled.fill(0)
  oled_topofScreenOffset = oled_topofScreen
  oled.text('LAN config:',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('starting webrepl',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled.show()
            
import webrepl
webrepl.start()    # start webrepl

if utelnetserverIsEnabled:
   if oledIsConnected:
     oled_topofScreenOffset = oled_topofScreenOffset + 10
     oled.text('starting utelnet server',oled_leftofScreenOffset ,oled_topofScreenOffset)
     oled.show()
   import utelnetserver
   utelnetserver.start()

if oledIsConnected:
  utime.sleep(10)
  #clear screen
  oled.fill(0)
  oled_topofScreenOffset = oled_topofScreen
  oled.show()
