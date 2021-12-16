# This file is executed on every boot (including wake-boot from deepsleep)

import esp
import uos
import machine
import gc
import ssd1306
import utime
from umqttsimple import MQTTClient
import ubinascii
import micropython
import network
import usyslog
from ntptime import settime

#uos.dupterm(None, 1) # disable REPL on UART(0)
esp.osdebug(None)
gc.collect()

oledIsConnected = False
addrOled = 60
addraddrOled = 60
SSD1306_Pin = 16      #oled_rst
Pin_high = 1
Pin_low = 0
i2c_scl = 15
i2c_sda = 4
oled_topofScreen = 0
oled_topofScreenOffset = 0
oled_leftofScreen = 0
oled_leftofScreenOffset = 0
APIsEnabled = False
utelnetserverIsEnabled = False

DataJson = {
  "APSSID" : "ssid",
  "APpassword" : "ssid_password",
  "STSSID" : "ssid",
  "STpassword" : "ssid_password",
  "mqtt_user" : "User",
  "mqtt_password" : "Pass",
  "syslog" : "ip"
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

import ujson
with open('config.json') as data_file:
   DataJson = ujson.load(data_file)
data_file.close

#Setup pins for SSD1306 Pin 16 is oled_rst
pin16 = machine.Pin(SSD1306_Pin, machine.Pin.OUT)
pin16.value(Pin_high)

#setup i2c pins 15 scl & 4  sda
i2c = machine.SoftI2C(scl=machine.Pin(i2c_scl),sda=machine.Pin(i2c_sda))

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
station.disconnect()
utime.sleep_ms(1000)
station.connect(str(DataJson["wifi"]["STSSID"]), str(DataJson["wifi"]["STpassword"]))
station.isconnected() 
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

if oledIsConnected:
  #clear screen
  oled.fill(0)
  oled_topofScreenOffset = oled_topofScreen
  oled.text('LAN config:',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled_topofScreenOffset = oled_topofScreenOffset + 10
  oled.text('starting webrepl',oled_leftofScreenOffset ,oled_topofScreenOffset)
  oled.show()
  
while station.isconnected() == False and station.active() == True:
    utime.sleep_ms(500)
# ntptime.host = 'time.nrc.ca'
settime()

# syslog stuff
## Test non-default facility
# s = usyslog.UDPClient(ip=SYSLOG_SERVER_IP, facility=usyslog.F_LOCAL4)
# s.info('LOCAL4:Info!')
# Test other methods
# s = usyslog.UDPClient(ip=SYSLOG_SERVER_IP)
# s.alert('Testing a message with alert severity')
# s.critical('This is a non critical test message!')
# s.error('In case of an error, you can use this severity.')
# s.debug('Debug messages can get annoying in production environments!')
# s.info('Informational messages are just slightly less "severe" than debug messages')
# s.notice('Noticed this? Nevermind!')
# s.warning('This is my last warning!')
# s.log(usyslog.S_EMERG, 'This is an emergency! Lets hope all prior tests did pass succesfully!')
syslog = usyslog.UDPClient(ip=DataJson["wifi"]["syslog"], facility=usyslog.F_LOCAL4)
syslog.info('CCS811 Booting')

            
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
  utime.sleep(5)
  #clear screen
  oled.fill(0)
  oled_topofScreenOffset = oled_topofScreen
  oled.show()
