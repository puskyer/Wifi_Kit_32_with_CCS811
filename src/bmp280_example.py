from machine import I2C, SoftI2C
from bmp280 import *

i2c_scl_pin = 15
i2c_sda_pin = 4

bus = SoftI2C(scl=machine.Pin(i2c_scl_pin),sda=machine.Pin(i2c_sda_pin))
bmp = BMP280(bus)

bmp.use_case(BMP280_CASE_WEATHER)
bmp.oversample(BMP280_OS_HIGH)

bmp.temp_os = BMP280_TEMP_OS_8
bmp.press_os = BMP280_PRES_OS_4

bmp.standby = BMP280_STANDBY_250
bmp.iir = BMP280_IIR_FILTER_2

bmp.spi3w = BMP280_SPI3W_ON

#bmp.power_mode = BMP280_POWER_FORCED
# or 
#bmp.force_measure()

bmp.power_mode = BMP280_POWER_NORMAL
# or 
#bmp.normal_measure()
# also
#bmp.in_normal_mode()

bmp.power_mode = BMP280_POWER_SLEEP
# or 
#bmp.sleep()

print(bmp.temperature)
print(bmp.pressure)

#True while measuring
bmp.is_measuring

#True while copying data to registers
bmp.is_updating