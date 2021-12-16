import dht, machine, ssd1306, utime, CCS811, ujson
from machine import Pin, I2C
from umqttsimple import MQTTClient
import ubinascii
import micropython

keepalive = 0
last_message = 0
message_interval = 10
counter = 0

addrOled = 60                # Wifi 32 kit oled I2C address 0x3c
addrSI7021 = 64              #  I2C address 0x40
addrCCS811 = 90              # CCS811_I2C_Address 0x5a
addrAT24C32 = 87             # AT24C32_I2C_Address 0x57
addrDS3231 = 104             # DS3231_I2C_ADDRESS 0x68
addrBMP280 = 118             #  I2C address 0x76 
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

#setup i2c pins 15 oled_scl & 4 oled_sda (CCS811 is on the same bus)
i2c = machine.I2C(scl=machine.Pin(i2c_scl_pin),sda=machine.Pin(i2c_sda_pin))

# Scan i2c bus and check if OLi2c = machine.I2C(scl=machine.Pin(i2c_scl_pin),sda=machine.Pin(i2c_sda_pin))DE display are connected
print('Scan i2c bus...')
devices = i2c.scan()
print(devices)

