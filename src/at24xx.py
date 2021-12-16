'''
    AT24C32 EEPROM drive

    Author: shaoziyang
    Date:   2018.3

    http://www.micropython.org.cn
'''
from machine import I2C

i2c_addr = (0x57)   # 87 dec

class AT24XX():
    def __init__(self, i2c, i2c_addr=0x57, pages=128, bpp=32):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.pages = pages
        self.bpp = bpp # bytes per page
        
    def capacity(self):
        """Storage capacity in bytes"""
        return self.pages * self.bpp    

    def write_byte(self, addr, dat):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr, dat]))

    def read_byte(self, addr):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr]))
        t = self.i2c.readfrom(i2c_addr, 1)
        return t[0]

    def write_word(self, addr, dat):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr, dat//256, dat]))

    def read_word(self, addr):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr]))
        t = self.i2c.readfrom(i2c_addr, 2)
        return t[0]*256 + t[1]

    def write_dword(self, addr, dat):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr, dat>>24, dat>>16, dat>>8, dat]))

    def read_dword(self, addr):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr]))
        t = self.i2c.readfrom(i2c_addr, 4)
        return (t[0]<<24) + (t[1]<<16) + (t[2]<<8) + t[3]

    def write_buf(self, addr, buf):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr]) + buf)
        
    def read_buf(self, addr, num):
        self.i2c.writeto(i2c_addr, bytearray([addr//256, addr]))
        return self.i2c.readfrom(i2c_addr, num)

