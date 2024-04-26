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
            
sw0 = Pin(9, Pin.IN, Pin.PULL_UP) # UP
sw1 = Pin(8, Pin.IN, Pin.PULL_UP) # SELECT
sw2 = Pin(7, Pin.IN, Pin.PULL_UP) # DOWN
        
        # Display Settings:
        
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)
        # Sensor
sensor = ADC(26)
sensor_history_size = 250
history = []
class HeartMonitor():
    
    def __init__(self):
        
        # main attribtes:
        
        # mainMenu attributes:
        
        self.menuTxtBpm 	= "Measure heart rate"
        self.menuTxtHrv		= "Basic HRV analysis"
        self.menuTxtHistory = "History"
        self.menuTxtKubios 	= "Kubios"
        
        # measure_heart_rate attributes:
        self.beats = 0
        self.beat = False
        
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
        pass
        
    def measure_heart_rate(self):
        global history
        sensor_data = sensor.read_u16()
        history.append(sensor_data)
        history = history[-sensor_history_size:]
        
        floor, roof = min(history), max(history)
        
        max_filter = (floor + roof * 3)//4
        min_filter = (floor + roof)//2
        
        
        if not self.beat and sensor_data > max_filter:
            self.beat = True
            self.beats += 1
            print(f"beat: {self.beat}, beats:{self.beats}, raw value: {sensor_data}")
        if self.beat and sensor_data < min_filter:
            self.beat = False
            print(f"beat: {self.beat}, beats:{self.beats}, raw value: {sensor_data}")
        
        
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
    device.measure_heart_rate()
        
