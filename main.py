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



        # Sensor:

sensor = ADC(26)
sensor_history_size = 250
history = []
timer = Timer(-1)
timer.deinit()
sensor_bool = False
class HeartMonitor():
    
    def __init__(self):
        
        # main attribtes:
        self.deviceState = "Main menu"
        self.buttonsAreUp = True
        
        # mainMenu attributes:
        
        self.menuTxtBpm 	= "Heart rate"
        self.menuTxtHrv		= "HRV analysis"
        self.menuTxtHistory = "History"
        self.menuTxtKubios 	= "Kubios"
        self.menuPointer = ">"
        self.menuState = 1
        
        # measure_heart_rate attributes:
        self.beats = 0
        self.beat = False
        self.UserBPMText = 0

        
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
    
    def checkButtonsAreUp(self):
        
        if sw0() == 1 and sw1() == 1 and sw2() == 1:
            
            self.buttonsAreUp = True
    
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
            
            
        if sw2() == 0 and  self.buttonsAreUp == True:
            
            if self.menuState == 1:
                
                self.menuState = 4
                self.buttonsAreUp = False 
            
            else:
                
                self.menuState -= 1
                self.buttonsAreUp = False 
                
        if sw0() == 0 and  self.buttonsAreUp == True:
            
            if self.menuState == 4:
                
                self.menuState = 1
                self.buttonsAreUp = False 
            
            else:
                
                self.menuState += 1
                self.buttonsAreUp = False 
                
        if sw1() == 0 and self.buttonsAreUp == True:
            
            if self.menuState == 1:
                
                timer.init(period=10000, mode=Timer.PERIODIC, callback=timer_callback)			#Timer päälle BPM laskua varten
                self.deviceState = "Measure heart rate"
                
            elif self.menuState == 2:
                pass
            
            elif self.menuState == 3:
                pass

            elif self.menuState == 4:
                pass
        
        self.checkButtonsAreUp()
        
    def measure_heart_rate(self):

        global history
        global sensor_history_size
        
        oled.text("BPM: ", 15, 50, 1)
        oled.show()
            
            
        

        sensor_data = sensor.read_u16()
        history.append(sensor_data)
        history = history[-sensor_history_size:]
        
        floor, roof = min(history), max(history)
        
        max_filter = (floor + roof * 3)//4
        min_filter = (floor + roof)//2
            
        if not self.beat and sensor_data > max_filter and sensor_data < 40000:
            self.beat = True
            self.beats += 1
            print(f"beat: {self.beat}, beats:{self.beats}, raw value: {sensor_data}")
            
        if self.beat and sensor_data < min_filter:
            self.beat = False
            print(f"beat: {self.beat}, beats:{self.beats}, raw value: {sensor_data}")
                
        if sw1() == 0 and self.buttonsAreUp == True:
            
            self.deviceState = "Main menu"
            
        self.checkButtonsAreUp()
        time.sleep_ms(2)
            
        
    def bpm_calc(self):
        
        oled.fill(0)
        print("callback")
        bpm = self.beats * 12
        self.beats = 0
        self.UserBPMText = "BPM: "+ str(bpm)
        oled.text(self.UserBPMText, 15, 50, 1)
        print(bpm)
        oled.show()
        
        
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

# Timer callback
def timer_callback(timer):
    
    device.bpm_calc()


while True:
    
    if device.deviceState == "Main menu":
        
        device.mainMenu()
        
    if device.deviceState == "Measure heart rate":
        
        device.measure_heart_rate()
        
    if device.deviceState == "Basic hrv analysis":
        
        device.basic_hrv_analysis()
        
    if device.deviceState == "History":
        
        device.history()
        
    if device.deviceState == "kubios":
        
        device.kubios()
    
