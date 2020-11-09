import si7021
import machine
i2c = machine.I2C(sda=machine.Pin(21),scl=machine.Pin(22))
 
temp_sensor = si7021.Si7021(i2c)
 
print('Serial:              {value}'.format(value=temp_sensor.serial))
print('Identifier:          {value}'.format(value=temp_sensor.identifier))
print('Temperature:         {value}'.format(value=temp_sensor.temperature))
print('Relative Humidity:   {value}'.format(value=temp_sensor.relative_humidity))

