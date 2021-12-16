'Quick example for the i2c driver.'

import si7021
import machine

i2c_scl_pin = 15
i2c_sda_pin = 4
i2c = machine.SoftI2C(scl=machine.Pin(i2c_scl_pin),sda=machine.Pin(i2c_sda_pin))

temp_sensor = si7021.Si7021(i2c)
print('Serial:              {value}'.format(value=temp_sensor.serial))
print('Identifier:          {value}'.format(value=temp_sensor.identifier))
print('Temperature:         {value}'.format(value=temp_sensor.temperature))
print('Relative Humidity:   {value}'.format(
    value=temp_sensor.relative_humidity))

temp_sensor.reset()
print('\nModule reset.\n')

print('Temperature:         {value}'.format(value=temp_sensor.temperature))
print('Relative Humidity:   {value}'.format(
    value=temp_sensor.relative_humidity))

print('Fahrenheit:          {value}'.format(
    value=si7021.convert_celcius_to_fahrenheit(temp_sensor.temperature)))
