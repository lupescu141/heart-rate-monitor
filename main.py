import fifo
import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import micropython
micropython.alloc_emergency_exception_buf(200)


class HeartMonitor():
    
    def __init__(self):
        
        # Hardware:
            
                # Buttons:
            
        self.sw0 = Pin(9, Pin.IN, Pin.PULL_UP)
        self.sw1 = Pin(8, Pin.IN, Pin.PULL_UP)
        self.sw2 = Pin(7, Pin.IN, Pin.PULL_UP)
        
                # Display Settings:
        
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled_width = 128
        self.oled_height = 64
        self.oled = SSD1306_I2C(oled_width, oled_height, i2c)
        
                # Attributes:
    
    def mainMenu(self):
        
    def beats_per_minute(self):
    
        
        