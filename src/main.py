import dht, machine, ssd1306, utime, CCS811, ujson
from machine import Pin, I2C
from umqttsimple import MQTTClient
import ubinascii
import micropython

DevIsEnabled = True

try:
    #if DataJson in globals():      #not working???
    #if DataJson in locals():       #not working???
    mqtt_user =  DataJson["wifi"]["mqtt_user"]
    mqtt_password =  DataJson["wifi"]["mqtt_password"]
    print("DataJson exists!")
except NameError:
    print("DataJson Did not exists!")
    DataJson = {
      "APSSID" : "ssid",
      "APpassword" : "ssid_password",
      "STSSID" : "ssid",
      "STpassword" : "ssid_password",
      "mqtt_user" : "User",
      "mqtt_password" : "Pass"  
    }
    import ujson
    with open('config.json') as data_file:
        DataJson = ujson.load(data_file)
    data_file.close
    mqtt_user =  DataJson["wifi"]["mqtt_user"]
    mqtt_password =  DataJson["wifi"]["mqtt_password"]
    print("DataJson Now exists!")


mqtt_server = '192.168.1.41'
mqtt_port = 1883
client_id = ubinascii.hexlify(machine.unique_id())

if DevIsEnabled:
   topic_sub = b'CCS811Dev/STATE'
   topic_pub = b'CCS811Dev/SENSOR'
else:    
   topic_sub = b'CCS811/STATE'
   topic_pub = b'CCS811/SENSOR'

keepalive = 0
last_message = 0
message_interval = 10
counter = 0

addrOled = 60                # Wifi 32 kit oled I2C address 0x3c
addrSI7021 = 64            #  I2C address 0x40
addrCCS811 = 90              # CCS811_I2C_Address 0x5a
addrAT24C32 = 87             # AT24C32_I2C_Address 0x57
addrDS3231 = 104             # DS3231_I2C_ADDRESS 0x68
addrBME280 = 118            #  I2C address 0x76 
ccs811IsConnected = False
oledIsConnected = False
AT24C32IsConnected = False
DS3231IsConnected = False
DHT22IsConnected = True

baseline_HB = 0
baseline_LB = 0
eCO2 = 0
tVOC = 0
pin_high = led_on = 1
pin_low = led_off = 0
led_pin = 25
oled_rst_pin = 16
CCS811_nWake_pin = 23
i2c_scl_pin = 15
i2c_sda_pin = 4
dht22_pin = 26
oled_x = oled_y = 0

mqttJson = {
  "Temperature" : "temperature",
  "Humidity" : "humidity",
  "eCO2ppm" : "eCO2",
  "tVOCppb" : "tVOC", 
  "Baseline_HB" : "baseline_HB",
  "Baseline_LB" : "baseline_LB",
  "Date" : "thedate",
  "Time" : "thetime",
  "Status" : "status"
  }

def sub_cb(topic, msg):
#  print((topic, msg))
  print('subscription %s msg %s ' % (topic, msg))
  if topic == topic_sub and msg == b'restart':
    print('ESP received restart message')
    msg = "ESP received restart message"
    client.publish(topic_sub, msg)
    utime.sleep(5)
    machine.reset()

def connect_and_subscribe():
  global client_id, mqtt_server, mqtt_port, mqtt_user, mqtt_password, topic_sub
  client = MQTTClient(client_id, mqtt_server, mqtt_port, mqtt_user, mqtt_password, keepalive)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker'% (mqtt_server))
  print('subscribed to %s topic ' % (topic_sub))
  msg = "Connected to MQTT broker "+str(mqtt_server)+"subscribed to %s topic "+str(topic_sub)
  client.publish(topic_pub, msg)
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  utime.sleep(5)
  machine.reset()

def blink_led(val):
  if val == "":
      val = 1
  Pin(led_pin, Pin.OUT).value(led_on)
  utime.sleep(val)
  Pin(led_pin, Pin.OUT).value(led_off)    
  print('LED blinked!')

#setup i2c pins 15 oled_scl & 4 oled_sda (CCS811 is on the same bus)
i2c = machine.I2C(scl=machine.Pin(i2c_scl_pin),sda=machine.Pin(i2c_sda_pin))

# Scan i2c bus and check if OLDE display are connected
print('Scan i2c bus...')
devices = i2c.scan()
if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))
  #utime.sleep(5)
  for device in devices: 
    if device == addrOled:
      oledIsConnected = True
      #Setup pins for SSD1306 Pin 16 is oled_rst
      oled_rst = machine.Pin(oled_rst_pin, machine.Pin.OUT)
      oled_rst.value(pin_high)
    elif device == addrCCS811:
      ccs811IsConnected = True
      #Setup pins for CCS811 Pin 23 is nWake must be low 
      CCS811_nWake = machine.Pin(CCS811_nWake_pin, machine.Pin.OUT)
      CCS811_nWake.value(pin_low)
    elif device == addrAT24C32:
      AT24C32IsConnected = True        
    elif device == addrDS3231:
      DS3231IsConnected = True

if oledIsConnected:
  #setup i2c for ssd1306
  oled = ssd1306.SSD1306_I2C(128,64,i2c)
  print('OLED is now setup on I2C address '+str(hex(addraddrOled)))  
  #clear screen
  oled.fill(0)
  oled.text('ESP32 Wifi Kit',oled_x,oled_y)
  oled.text(' OLED is setup',oled_x,oled_y+10)
  oled.show()

if ccs811IsConnected:
  # Adafruit sensor breakout has i2c addr: 90; Sparkfun: 91
  s = CCS811.CCS811(i2c=i2c, addr=addrCCS811)
  print('CCS811 is now setup on I2C address '+str(hex(addrCCS811)))
  if oledIsConnected:
     oled.text(' CCS811 is setup',oled_x,oled_y+20)
     oled.show()
  
if DS3231IsConnected:
  from ds3231_port import DS3231
  ds3231 = DS3231(i2c=i2c)
  print('DS3231 is now setup on I2C address '+str(hex(addrDS3231)))
  if oledIsConnected:
     oled.text(' DS3231 is setup',oled_x,oled_y+30)
     oled.show()
  ds3231.get_time()

if AT24C32IsConnected:
  import at24c32n
  eeprom = at24c32n.AT24C32N(i2c)
  print('AT24C32N is now setup  on I2C address '+str(hex(addrAT24C32)))
  if oledIsConnected:
     oled.text(' AT24C32N is setup',oled_x,oled_y+40)
     oled.show()

try:
  if oledIsConnected:
     #clear screen
     oled.fill(0)
     oled.show()
  blink_led(2)
  client = connect_and_subscribe()
  if DHT22IsConnected:
     sensor = dht.DHT22(machine.Pin(dht22_pin))
     sensor.measure()
     mqttJson["Temperature"] = sensor.temperature()
     mqttJson["Humidity"] = sensor.humidity()
     if oledIsConnected:
        #clear screen
        oled.fill(0)
        oled.text('temp:     '+str(mqttJson["Temperature"])+' C',oled_x,oled_y)
        oled.text('humidity: '+str(mqttJson["Humidity"])+' %',oled_x,oled_y+10)
        oled.show() 
  if ccs811IsConnected:
     if DHT22IsConnected:
        # give environemnt data - put_envdata(self,humidity,temp):
        s.put_envdata(mqttJson["Humidity"],mqttJson["Temperature"])
     baseline=bytearray(s.get_baseline())
     mqttJson["Baseline_HB"] = baseline[0]
     mqttJson["Baseline_LB"] = baseline[1]
     if oledIsConnected:
        oled.text('CCS811 baseline is ',oled_x,oled_y+30)
        oled.text('HB '+str(mqttJson["Baseline_HB"])+' LB '+str(mqttJson["Baseline_LB"]),oled_x,oled_y+40)
        oled.show()
  utime.sleep(5)
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    client.check_msg()
    if (utime.time() - last_message) > message_interval:
       mytime = utime.localtime()
       mqttJson["Date"] = str(mytime[0])+'/'+str(mytime[1])+'/'+str(mytime[2])
       mqttJson["Time"] = str(mytime[3])+':'+str(mytime[4])+':'+str(mytime[5])+' UTC'
       if DHT22IsConnected:
          sensor.measure()
          mqttJson["Temperature"] = sensor.temperature()
          mqttJson["Humidity"] = sensor.humidity()
          if oledIsConnected:
             #clear screen
             oled.fill(0)
             oled.text('temp:     '+str(mqttJson["Temperature"])+' C',oled_x,oled_y)
             oled.text('humidity: '+str(mqttJson["Humidity"])+' %',oled_x,oled_y+10)
             oled.show()
       if ccs811IsConnected:
          if s.data_ready():
             mqttJson["eCO2ppm"] = s.eCO2
             mqttJson["tVOCppb"] = s.tVOC
             thefulldatetime = mqttJson["Date"]+" "+mqttJson["Time"]
             print('eCO2: %d ppm, TVOC: %d ppb time: %s' % (mqttJson["eCO2ppm"], mqttJson["tVOCppb"], thefulldatetime))     
             if oledIsConnected:
                oled.text('eCO2 ppm: '+str(mqttJson["eCO2ppm"]),oled_x,oled_y+20)
                oled.text('TVOC ppb: '+str(mqttJson["tVOCppb"]),oled_x,oled_y+30)
                oled.text('Date: '+mqttJson["Date"],oled_x,oled_y+40)
                oled.text('Time: '+mqttJson["Time"],oled_x,oled_y+50)             
                oled.show()
             if (utime.time() - last_message) > 3600:
                if DHT22IsConnected:
                   # refresh environemnt data every hour - humidity & temp
                   s.put_envdata(mqttJson["Humidity"],mqttJson["Temperature"])
                # lets also get the baseline bytes
                baseline=bytearray(s.get_baseline())
                mqttJson["Baseline_HB"] = baseline[0]
                mqttJson["Baseline_LB"] = baseline[1]
                if oledIsConnected:
                   #clear screen
                   oled.fill(0)
                   oled.text('HB '+str(mqttJson["Baseline_HB"])+' LB '+str(mqttJson["Baseline_LB"]),oled_x,oled_y+40)
                   oled.show()
       last_message = utime.time()
       JsonMqtt = ujson.dumps(mqttJson)
       print(JsonMqtt)
       client.publish(topic_pub, JsonMqtt)   
    utime.sleep(5)
    if oledIsConnected:
       oled.fill(0)
       oled.show()    
  except OSError as e:
    restart_and_reconnect()
