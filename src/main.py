import micropython, dht, machine, ssd1306, utime, CCS811, ujson, si7021, ubinascii, struct
from bmp280 import *
from machine import Pin, SoftI2C
# from umqttsimple import MQTTClient
#from umqtt.simple import MQTTClient
from umqtt.robust import MQTTClient
from ntptime import settime

DevIsEnabled = False

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
      "mqtt_password" : "Pass",
      "syslog" : "192.168.2.1"  
    }
    with open('config.json') as data_file:
        DataJson = ujson.load(data_file)
    data_file.close
    mqtt_user =  DataJson["wifi"]["mqtt_user"]
    mqtt_password =  DataJson["wifi"]["mqtt_password"]
    print("DataJson Now exists!")

mqtt_server = '192.168.2.41'
mqtt_port = 1883
client_id = ubinascii.hexlify(machine.unique_id())

if DevIsEnabled:
   topic_sub = b'CCS811Dev/STATE'
   topic_pub = b'CCS811Dev/SENSOR'
else:    
   topic_sub = b'CCS811/STATE'
   topic_pub = b'CCS811/SENSOR'

keepalive = 30
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
DHT22IsConnected = False

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

at24xx_index=0                                # 4 Bytes
bmp_temperature_index=4                       # 4 Bytes
bmp_Barometric_pressure_index=8               # 4 Bytes
si7021_temperature_index=12                   # 4 Bytes
si7021_relative_humidity_index=16             # 4 Bytes
ccs811_eCO2ppm_index=20                       # 4 Bytes
ccs811_tVOCppb_index=24                       # 4 Bytes
ccs811_baseline_index=28                      # 2 Bytes (1 word)
ds3231temp_index = 31

mqttJson = {
  "si7021": {
           "Temperature" : 20.0,
           "Temperature_units" : "C",
           "Humidity" : 50.0
           },
  "bmp280": {
           "Temperature" : 20.0,
           "Temperature_Units" : "C",
           "Barometric_Pressure" : 100.0,
           "Barometric_Pressure_Units" : "inches-Hg"
           },
  "ccs811": {
           "eCO2ppm" : "eCO2",
           "tVOCppb" : "tVOC",
           "Baseline_HB" : "baseline_HB",
           "Baseline_LB" : "baseline_LB",
           },
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
  if topic == topic_sub and msg == b'status':
    print('ESP received status message')
    msg = "ESP received status message"
    client.publish(topic_sub, msg)
    client.publish(topic_pub, JsonMqtt)    

# MQTT Connect Return code values
# Value Return  Response                                        Description
#       Code 
# 0     0x00 Connection Accepted                                Connection accepted
# 1     0x01 Connection Refused, unacceptable protocol version  The Server does not support the level of the MQTT protocol requested by the Client
# 2     0x02 Connection Refused, identifier rejected            The Client identifier is correct UTF-8 but not allowed by the Server
# 3     0x03 Connection Refused, Server unavailable             The Network Connection has been made but the MQTT service is unavailable
# 4     0x04 Connection Refused, bad user name or password      The data in the user name or password is malformed
# 5     0x05 Connection Refused, not authorized                 The Client is not authorized to connect
# 6-255                                                         Reserved for future use

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


try:
    syslog = usyslog.UDPClient(ip=DataJson["wifi"]["syslog"], facility=usyslog.F_LOCAL4)
    syslog.info('CCS811 Main started!')
    print("Start Sysloging from Main!")
except NameError:
    import usyslog
    syslog = usyslog.UDPClient(ip=DataJson["wifi"]["syslog"], facility=usyslog.F_LOCAL4)
    syslog.info('CCS811 usyslog started!')

#setup i2c pins 15 oled_scl & 4 oled_sda (CCS811 is on the same bus)
i2c = machine.SoftI2C(scl=machine.Pin(i2c_scl_pin),sda=machine.Pin(i2c_sda_pin))

# Scan i2c bus and check if OLDE display are connected
print('Scan i2c bus...')
devices = i2c.scan()
if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))
  #utime.sleep(5)
  for device in devices:
     if device == addrAT24C32:
            AT24C32IsConnected = True
            import at24xx
            eeprom = at24xx.AT24XX(i2c)
            print('AT24C32N is now setup  on I2C address '+str(addrAT24C32)+' '+str(hex(addrAT24C32)))
            print('AT24C32N Capacity is '+str(eeprom.capacity())+' '+str(hex(eeprom.capacity())))
            # now that eeprom is ready, lets save the time & date to it.
            mytime=(utime.mktime(utime.localtime()))
            eeprom.write_dword(at24xx_index,(mytime))  
            if oledIsConnected:
               oled.text(' AT24C32N is setup',oled_x,oled_y+40)
               oled.show()

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
      #setup i2c for ssd1306
      oled = ssd1306.SSD1306_I2C(128,64,i2c)
      print('OLED is now setup on I2C address '+str(addraddrOled)+' '+str(hex(addraddrOled)))  
      #clear screen
      oled.fill(0)
      oled.text('ESP32 Wifi Kit',oled_x,oled_y)
      oled.text(' OLED is setup',oled_x,oled_y+10)
      oled.show()      
    elif device == addrCCS811:
      ccs811IsConnected = True
      #Setup pins for CCS811 Pin 23 is nWake must be low 
      CCS811_nWake = machine.Pin(CCS811_nWake_pin, machine.Pin.OUT)
      CCS811_nWake.value(pin_low)
      # Adafruit sensor breakout has i2c addr: 90; Sparkfun: 91
      s = CCS811.CCS811(i2c=i2c, addr=addrCCS811)
      print('CCS811 is now setup on I2C address '+str(addrCCS811)+' '+str(hex(addrCCS811)))
      if oledIsConnected:
         oled.text(' CCS811 is setup',oled_x,oled_y+20)
         oled.show()
    elif device == addrDS3231:
      DS3231IsConnected = True
      from ds3231_port import DS3231
      ds3231 = DS3231(i2c=i2c)
      print('DS3231 is now setup on I2C address '+str(addrDS3231)+' '+str(hex(addrDS3231)))
      if oledIsConnected:
         oled.text(' DS3231 is setup',oled_x,oled_y+30)
         oled.show()
      ds3231temp = ds3231.get_temperature()
      eeprom.write_dword(ds3231temp_index,int(ds3231temp))
      print('DS3231 Temp is '+str(ds3231temp))
      #print('DS3231 pre test is '+str(ds3231.rtc_test()))
      ## ds3231.get_time()
      #print('DS3231 post test is '+str(ds3231.rtc_test()))      
      ds3231.save_time()      
    elif device == addrBME280:
        # Temperature is calculated in degrees C, you can convert this to F by using the classic
        # F = C * 9/5 + 32 equation.
        # Pressure is returned in the SI units of Pascals. 100 Pascals = 1 hPa = 1 millibar. Often
        # times barometric pressure is reported in millibar or inches-mercury. For future
        # reference 1 pascal =0.000295333727 inches of mercury, or 1 inch Hg = 3386.39
        # Pascal. So if you take the pascal value of say 100734 and divide by 3389.39 you'll get
        # 29.72 inches-Hg.
        BME280IsConnected = True
        bmp = BMP280(i2c)
        bmp_temperature=round(bmp.temperature,1)
        bmp_pressure=round((bmp.pressure/3386.39),1)
        #eeprom.write_dword(bmp_temperature_index,bmp_temperature)
        #eeprom.write_dword(bmp_Barometric_pressure_index,bmp_pressure)
        print('BMP280 is now setup on I2C address '+str(addrBME280)+' '+str(hex(addrBME280)))
        print('BMP280 Temperature is '+str(bmp_temperature)+' Degrees C / '+str(round(((bmp_temperature/1.8)+32),1))+' Degrees F')
        print('BMP280 Barometric Pressure is '+str(bmp_pressure)+" inches-Hg")
    elif device == addrSI7021:
        SI7021IsConnected = True
        temp_sensor = si7021.Si7021(i2c)
        si7021_serial=str(temp_sensor.serial)
        si7021_identifier=str(temp_sensor.identifier)
        si7021_temperature=round(temp_sensor.temperature,1)
        si7021_relative_humidity=round(temp_sensor.relative_humidity,1)
        eeprom_si7021_temperature = struct.pack('f', si7021_temperature)
        eeprom_si7021_relative_humidity = struct.pack('f', si7021_relative_humidity)
        #print(si7021_temperature)
        #print(si7021_relative_humidity)
        #print(eeprom_si7021_temperature)
        #print(eeprom_si7021_relative_humidity)
        #print(bytes(eeprom_si7021_temperature))
        #print(bytes(eeprom_si7021_relative_humidity))
        #eeprom.write_dword(si7021_temperature_index,eeprom_si7021_temperature)
        #eeprom.write_dword(si7021_relative_humidity_index,eeprom_si7021_relative_humidity)
        print('si7021 is now setup on I2C address '+str(addrSI7021)+' '+str(hex(addrSI7021)))
        print('Serial:              {value}'.format(value=si7021_serial))
        print('Identifier:          {value}'.format(value=si7021_identifier))
        print('Temperature:         {value}'.format(value=si7021_temperature))
        print('Relative Humidity:   {value}'.format(value=si7021_relative_humidity))
        temp_sensor.reset()
        print('\nModule reset.\n')


try:
  if oledIsConnected:
     #clear screen
     oled.fill(0)
     oled.show()
  blink_led(2)
  client = connect_and_subscribe()
  if SI7021IsConnected:
     mqttJson["si7021"]["Temperature"] = round(temp_sensor.temperature,1)
     mqttJson["si7021"]["Humidity"] = round(temp_sensor.relative_humidity,1)
  if BME280IsConnected:
     mqttJson["bmp280"]["Temperature"] = round(bmp.temperature,1)
     mqttJson["bmp280"]["Barometric_Pressure"] = round((bmp.pressure/3386.39),1)
  if oledIsConnected:
     #clear screen
     oled.fill(0)
     oled.text('temp:     '+str(mqttJson["si7021"]["Temperature"])+' C',oled_x,oled_y)
     oled.text('humidity: '+str(mqttJson["si7021"]["Humidity"])+' %',oled_x,oled_y+10)
     oled.text('temp2: '+str(mqttJson["bmp280"]["Temperature"])+' %',oled_x,oled_y+11)
     oled.text('Barometric_pressure: '+str(mqttJson["bmp280"]["Barometric_Pressure"])+' %',oled_x,oled_y+12)
     oled.show()    
  if ccs811IsConnected:
     # give environemnt data - put_envdata(self,humidity,temp):
     s.put_envdata(mqttJson["si7021"]["Humidity"],mqttJson["si7021"]["Temperature"])
     baseline=bytearray(s.get_baseline())
     mqttJson["ccs811"]["Baseline_HB"] = baseline[0]
     mqttJson["ccs811"]["Baseline_LB"] = baseline[1]
     if oledIsConnected:
        oled.text('CCS811 baseline is ',oled_x,oled_y+30)
        oled.text('HB '+str(mqttJson["ccs811"]["Baseline_HB"])+' LB '+str(mqttJson["ccs811"]["Baseline_LB"]),oled_x,oled_y+40)
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
       if SI7021IsConnected:
          mqttJson["si7021"]["Temperature"] = round(temp_sensor.temperature,1)
          mqttJson["si7021"]["Humidity"] = round(temp_sensor.relative_humidity,1)
       if BME280IsConnected:
          mqttJson["bmp280"]["Temperature"] = round(bmp.temperature,1)
          mqttJson["bmp280"]["Barometric_Pressure"] = round((bmp.pressure/3386.39),1)
       if oledIsConnected:
          #clear screen
          oled.fill(0)
          oled.text('temp:     '+str(mqttJson["si7021"]["Temperature"])+' C',oled_x,oled_y)
          oled.text('humidity: '+str(mqttJson["si7021"]["Humidity"])+' %',oled_x,oled_y+10)
          oled.text('temp2: '+str(mqttJson["bmp280"]["Temperature"])+' %',oled_x,oled_y+11)
          oled.text('Barometric_pressure: '+str(mqttJson["bmp280"]["Barometric_Pressure"])+' %',oled_x,oled_y+12)
          oled.show() 
       if ccs811IsConnected:
          if s.data_ready():
             mqttJson["ccs811"]["eCO2ppm"] = s.eCO2
             mqttJson["ccs811"]["tVOCppb"] = s.tVOC
             thefulldatetime = mqttJson["Date"]+" "+mqttJson["Time"]
             print('eCO2: %d ppm, TVOC: %d ppb time: %s' % (mqttJson["ccs811"]["eCO2ppm"], mqttJson["ccs811"]["tVOCppb"], thefulldatetime))     
             if oledIsConnected:
                oled.text('eCO2 ppm: '+str(mqttJson["ccs811"]["eCO2ppm"]),oled_x,oled_y+20)
                oled.text('TVOC ppb: '+str(mqttJson["ccs811"]["tVOCppb"]),oled_x,oled_y+30)
                oled.text('Date: '+mqttJson["Date"],oled_x,oled_y+40)
                oled.text('Time: '+mqttJson["Time"],oled_x,oled_y+50)             
                oled.show()
             if (utime.time() - last_message) > 3600:
                # refresh environemnt data every hour - humidity & temp
                s.put_envdata(mqttJson["si7021"]["Humidity"],mqttJson["si7021"]["Temperature"])
                # lets also get the baseline bytes
                baseline=bytearray(s.get_baseline())
                mqttJson["ccs811"]["Baseline_HB"] = baseline[0]
                mqttJson["ccs811"]["Baseline_LB"] = baseline[1]
                if oledIsConnected:
                   #clear screen
                   oled.fill(0)
                   oled.text('HB '+str(mqttJson["ccs811"]["Baseline_HB"])+' LB '+str(mqttJson["ccs811"]["Baseline_LB"]),oled_x,oled_y+40)
                   oled.show()
       blink_led(1)                   
       JsonMqtt = ujson.dumps(mqttJson)
       print(JsonMqtt)
       syslog.info(JsonMqtt)
       client.publish(topic_pub, JsonMqtt)
       last_message = utime.time()
    utime.sleep(5)
    if oledIsConnected:
       oled.fill(0)
       oled.show()    
  except OSError as e:
    restart_and_reconnect()
