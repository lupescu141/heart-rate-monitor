import fifo
import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import micropython
import ujson 
micropython.alloc_emergency_exception_buf(200)


# Hardware:
            
        # Buttons:
            
sw0 = Pin(9, Pin.IN, Pin.PULL_UP)
sw1 = Pin(8, Pin.IN, Pin.PULL_UP)
sw2 = Pin(7, Pin.IN, Pin.PULL_UP)
        
        # Display Settings:
        
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


class HeartMonitor():
    
    def __init__(self):
        
        # main attribtes:
        
        # mainMenu attributes:
        
        self.menuTxtBpm 	= "Measure heart rate"
        self.menuTxtHrv		= "Basic HRV analysis"
        self.menuTxtHistory = "History"
        self.menuTxtKubios 	= "Kubios"
        
        # measure_heart_rate attributes:
        
        # basic_hrv_analysis attributes:
        
        self.meanPPI 	= 0
        self.meanHR 	= 0
        self.RMSSD 		= 0
        self.SDNN 		= 0
        
        # history attributes:
        
        # kubios attributes:
        
        self.dataset = { 
                    "type": "RRI", 
                    "data": intervals, 
                    "analysis": {"type": "readiness"}
                    } 
        
        # sendData_MQTT attributes:
        
    
    def mainMenu(self):
        
        
    def measure_heart_rate(self):
        
        
    def basic_hrv_analysis(self):
        
        
    def history(self):
        
        
    def kubios(self):
        
        
    def sendData_MQTT(self):
        
        
        
# Main Loop:

while True:
    
        