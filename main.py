import fifo
import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
import micropython
import urequests as requests  
import ujson 
import network 
micropython.alloc_emergency_exception_buf(200)


# Hardware:
            
        # Buttons:
            
sw0 = Pin(9, Pin.IN, Pin.PULL_UP) # Down
sw1 = Pin(8, Pin.IN, Pin.PULL_UP) # SELECT
sw2 = Pin(7, Pin.IN, Pin.PULL_UP) # UP
        
        # Display Settings:
        
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


class HeartMonitor():
    
    def __init__(self):
        
        # main attribtes:
        
        # mainMenu attributes:
        
        self.menuTxtBpm 	= "Heart rate"
        self.menuTxtHrv		= "HRV analysis"
        self.menuTxtHistory = "History"
        self.menuTxtKubios 	= "Kubios"
        self.menuPointer = ">"
        self.menuState = 1
        
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
                    "data": "intervals", 
                    "analysis": {"type": "readiness"}
                    } 
        
        # sendData_MQTT attributes:
        
    
    def mainMenu(self):
        
        time.sleep(0.05)
        oled.text(self.menuTxtBpm, 15, 2, 1)
        oled.text(self.menuTxtHrv, 15, 15, 1)
        oled.text(self.menuTxtHistory, 15, 28, 1)
        oled.text(self.menuTxtKubios, 15, 41, 1)
        oled.show()
        
        if self.menuState == 1:
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 2, 1)

        elif self.menuState == 2:
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 15, 1)
            
        elif self.menuState == 3:
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 28, 1)

        elif self.menuState == 4:
            oled.fill_rect(0, 0, 10, 64, 0)
            oled.text(self.menuPointer, 2, 41, 1)
            
        if sw2() == 0:
            
            if self.menuState == 1:
                
                self.menuState = 4
            
            else:
                
                self.menuState -= 1
                
        if sw0() == 0:
            
            if self.menuState == 4:
                
                self.menuState = 1
            
            else:
                
                self.menuState += 1
                
        if sw1() == 0:
            
            if self.menuState == 1:
                pass
                
            elif self.menuState == 2:
                pass
            
            elif self.menuState == 3:
                pass

            elif self.menuState == 4:
                pass
        
    def measure_heart_rate(self):
        pass
        
    def basic_hrv_analysis(self):
        pass
        
        
    def history(self):
        pass
        
        
    def kubios(self):
        pass
        
        
    def sendData_MQTT(self):
        pass
        
        
# Main Loop:
device = HeartMonitor()

while True:
    device.mainMenu()
        